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

    def test_saving_language_preserves_selected_theme(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config_file = Path(temporary) / "config.json"
            with patch.object(miltop, "CONFIG_FILE", config_file):
                miltop.save_theme("purple")
                miltop.save_language("en")
                self.assertEqual(miltop.load_config(), {"theme": "purple", "language": "en"})

    def test_translations_contain_same_keys(self) -> None:
        self.assertEqual(set(miltop.TEXTS["pl"]), set(miltop.TEXTS["en"]))

    def test_package_version_matches_application(self) -> None:
        metadata = tomllib.loads(Path("pyproject.toml").read_text())
        self.assertEqual(metadata["project"]["version"], miltop.VERSION)


if __name__ == "__main__":
    unittest.main()
