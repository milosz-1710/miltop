import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

import miltop


class HardwareDetectionTests(unittest.TestCase):
    def test_parses_unprivileged_inxi_memory_details(self) -> None:
        output = """
        Memory:
          System RAM: total: 16 GiB
          Device-1: ChannelA-DIMM0 type: DDR4 size: 8 GiB speed: 2400 MT/s
            manufacturer: Samsung part-no: M471A1K43CB1-CRC serial: <filter>
          Device-2: ChannelB-DIMM0 type: DDR4 size: 8 GiB speed: 2400 MT/s
            manufacturer: Samsung part-no: M471A1K43CB1-CRC serial: <filter>
        """
        completed = subprocess.CompletedProcess([], 0, stdout=output, stderr="")
        with patch("miltop.subprocess.run", return_value=completed):
            hardware, model = miltop.Sampler._read_memory_hardware()
        self.assertEqual(hardware, "DDR4 • 2400 MT/s • 2×8 GiB")
        self.assertEqual(model, "Samsung M471A1K43CB1-CRC")

    def test_missing_inxi_has_safe_fallback(self) -> None:
        with patch("miltop.subprocess.run", side_effect=FileNotFoundError):
            self.assertEqual(miltop.Sampler._read_memory_hardware(), ("", ""))

    def test_parses_pci_gpu_vendor_and_model(self) -> None:
        output = '0000:00:02.0 "VGA compatible controller [0300]" "Intel Corporation [8086]" "WhiskeyLake-U GT2 [UHD Graphics 620] [3ea0]"\n'
        completed = subprocess.CompletedProcess([], 0, stdout=output, stderr="")
        with patch("miltop.subprocess.run", return_value=completed):
            devices = miltop.Sampler._pci_gpu_names()
        self.assertEqual(
            devices["0000:00:02.0"],
            ("Intel Corporation", "WhiskeyLake-U GT2 [UHD Graphics 620]"),
        )

    def test_detects_real_cards_and_ignores_drm_connectors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pci = root / "0000:00:02.0"
            pci.mkdir()
            (pci / "vendor").write_text("0x8086\n")
            (pci / "device").write_text("0x3ea0\n")
            (pci / "gpu_busy_percent").write_text("17\n")
            card = root / "card1"
            card.mkdir()
            (card / "device").symlink_to(pci, target_is_directory=True)
            (root / "card1-HDMI-A-1").mkdir()

            names = {"0000:00:02.0": ("Intel Corporation", "UHD Graphics 620")}
            with patch.object(miltop.Sampler, "_pci_gpu_names", return_value=names):
                devices = miltop.Sampler._find_gpus(root)

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].name, "Intel Corporation UHD Graphics 620")
        self.assertEqual(devices[0].kind, "integrated")
        self.assertEqual(devices[0].card, "card1")

    def test_gpu_kind_distinguishes_common_integrated_and_dedicated_cards(self) -> None:
        self.assertEqual(miltop.Sampler._gpu_kind("0x8086", "UHD Graphics 620", "0000:00:02.0", 0), "integrated")
        self.assertEqual(miltop.Sampler._gpu_kind("0x10de", "GeForce RTX 4070", "0000:01:00.0", 0), "dedicated")
        self.assertEqual(miltop.Sampler._gpu_kind("0x1002", "Radeon RX 7800 XT", "0000:03:00.0", 16 * 1024 ** 3), "dedicated")

    def test_reads_gpu_usage_from_drm_fdinfo_engine_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            proc_root = Path(temporary)
            fdinfo = proc_root / "123" / "fdinfo" / "5"
            fdinfo.parent.mkdir(parents=True)
            descriptor = proc_root / "123" / "fd" / "5"
            descriptor.parent.mkdir(parents=True)
            descriptor.symlink_to("/dev/dri/renderD128")
            fdinfo.write_text(
                "drm-client-id:\t8\n"
                "drm-pdev:\t0000:00:02.0\n"
                "drm-engine-render:\t1000000000 ns\n"
            )
            sampler = miltop.Sampler.__new__(miltop.Sampler)
            sampler.previous_gpu_engines = {}
            sampler.gpu_usage_checked = 0.0
            sampler.cached_fdinfo_usage = {}
            self.assertEqual(sampler._read_fdinfo_gpu_usage(10.0, proc_root), {})
            fdinfo.write_text(
                "drm-client-id:\t8\n"
                "drm-pdev:\t0000:00:02.0\n"
                "drm-engine-render:\t1250000000 ns\n"
            )
            usage = sampler._read_fdinfo_gpu_usage(11.0, proc_root)
        self.assertAlmostEqual(usage["0000:00:02.0"], 25.0)
        self.assertAlmostEqual(sampler.cached_process_gpu_usage[123], 25.0)

    def test_parses_nvidia_usage_temperature_memory_and_clocks(self) -> None:
        output = "00000000:01:00.0, 42, 61, 2048, 8192, 1500, 2100\n"
        completed = subprocess.CompletedProcess([], 0, stdout=output, stderr="")
        with patch("miltop.subprocess.run", return_value=completed):
            metrics = miltop.Sampler._read_nvidia_metrics()["0000:01:00.0"]
        self.assertEqual(metrics["usage"], 42.0)
        self.assertEqual(metrics["temperature"], 61.0)
        self.assertEqual(metrics["vram_total"], 8192 * 1024 ** 2)
        self.assertEqual(metrics["frequency_max"], 2100.0)

    def test_reads_battery_model_health_and_power(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            battery = Path(temporary) / "BAT0"
            battery.mkdir()
            values = {
                "type": "Battery", "present": "1", "manufacturer": "Fujitsu",
                "model_name": "CP778921-01", "technology": "Li-ion",
                "status": "Discharging", "capacity": "50", "cycle_count": "165",
                "charge_now": "2000000", "charge_full": "3000000",
                "charge_full_design": "4000000", "current_now": "1000000",
                "voltage_now": "10000000",
            }
            for name, value in values.items():
                (battery / name).write_text(value + "\n")
            devices = miltop.Sampler._read_batteries(Path(temporary))
        self.assertEqual(devices[0].model, "CP778921-01")
        self.assertEqual(devices[0].cycles, 165)
        self.assertAlmostEqual(devices[0].health or 0, 75.0)
        self.assertAlmostEqual(devices[0].power or 0, 10.0)

    def test_process_search_and_all_sort_modes(self) -> None:
        app = miltop.MiltopApp.__new__(miltop.MiltopApp)
        app.snapshot = miltop.Snapshot(processes=[
            miltop.ProcessRow(2, "zebra", 2.0, 100, gpu=40.0, energy=20.0),
            miltop.ProcessRow(1, "Alpha", 9.0, 50, gpu=5.0, energy=30.0),
        ])
        app.search_query = ""
        app.sort_mode = "cpu"
        self.assertEqual([row.pid for row in app.sorted_processes()], [1, 2])
        self.assertEqual([row.pid for row in app.sorted_processes("ram")], [2, 1])
        self.assertEqual([row.pid for row in app.sorted_processes("name")], [1, 2])
        self.assertEqual([row.pid for row in app.sorted_processes("gpu")], [2, 1])
        self.assertEqual([row.pid for row in app.sorted_processes("energy")], [1, 2])
        app.search_query = "zeb"
        self.assertEqual([row.pid for row in app.sorted_processes()], [2])

    def test_saving_language_preserves_selected_theme(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config_file = Path(temporary) / "config.json"
            with patch.object(miltop, "CONFIG_FILE", config_file):
                miltop.save_theme("purple")
                miltop.save_language("en")
                self.assertEqual(miltop.load_config(), {"theme": "purple", "language": "en"})

    def test_process_column_visibility_is_persistent_and_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config_file = Path(temporary) / "config.json"
            with patch.object(miltop, "CONFIG_FILE", config_file):
                miltop.save_process_columns(["ram", "not-a-column", "gpu"])
                self.assertEqual(miltop.load_process_columns(), ["ram", "gpu"])

    def test_translations_contain_same_keys(self) -> None:
        self.assertEqual(set(miltop.TEXTS["pl"]), set(miltop.TEXTS["en"]))

    def test_package_version_matches_application(self) -> None:
        metadata = tomllib.loads(Path("pyproject.toml").read_text())
        self.assertEqual(metadata["project"]["version"], miltop.VERSION)


if __name__ == "__main__":
    unittest.main()
