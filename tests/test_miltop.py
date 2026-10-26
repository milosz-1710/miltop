import subprocess
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

    def test_translations_contain_same_keys(self) -> None:
        self.assertEqual(set(miltop.TEXTS["pl"]), set(miltop.TEXTS["en"]))

    def test_package_version_matches_application(self) -> None:
        metadata = tomllib.loads(Path("pyproject.toml").read_text())
        self.assertEqual(metadata["project"]["version"], miltop.VERSION)


if __name__ == "__main__":
    unittest.main()
