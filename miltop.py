#!/usr/bin/env python3
"""miltop - prosty, kafelkowy menedzer zasobow dla terminala."""

from __future__ import annotations

import argparse
import curses
import json
import locale
import math
import os
import re
import shlex
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psutil


VERSION = "1.3.0"
BLOCKS = " ▁▂▃▄▅▆▇█"
CONFIG_FILE = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "miltop" / "config.json"
THEME_NAMES = ("cyan", "green", "red", "blue", "purple", "amber")
PROCESS_COLUMN_NAMES = ("cpu", "ram", "gpu", "energy")
LOGO = (
    "███╗   ███╗██╗██╗  ████████╗ ██████╗ ██████╗ ",
    "████╗ ████║██║██║  ╚══██╔══╝██╔═══██╗██╔══██╗",
    "██╔████╔██║██║██║     ██║   ██║   ██║██████╔╝",
    "██║╚██╔╝██║██║██║     ██║   ██║   ██║██╔═══╝ ",
    "██║ ╚═╝ ██║██║███████╗██║   ╚██████╔╝██║      ",
    "╚═╝     ╚═╝╚═╝╚══════╝╚═╝    ╚═════╝ ╚═╝      ",
)

TEXTS: dict[str, dict[str, str]] = {
    "pl": {
        "system_manager": "Menedżer systemu",
        "uptime": "Czas pracy",
        "refresh": "odświeżanie",
        "components": "PODZESPOŁY",
        "processor": "Procesor",
        "threads": "{count} wątków",
        "logical_cpu": "{count} logicznych CPU",
        "cpu_topology": "{cores} rdzenie • {threads} wątków",
        "load": "obciążenie",
        "gpu_usage": "Użycie układu graficznego",
        "graphics": "Grafika",
        "integrated_gpu": "Zintegrowana",
        "dedicated_gpu": "Dedykowana",
        "unknown_gpu": "Typ nierozpoznany",
        "detected_gpus": "Wykryte układy graficzne",
        "usage_unavailable": "użycie niedostępne",
        "temperature": "Temperatura",
        "frequency": "Taktowanie",
        "video_memory": "Pamięć grafiki",
        "shared_memory": "współdzielona z RAM",
        "driver": "Sterownik",
        "measurement": "Pomiar",
        "battery": "Bateria",
        "battery_not_detected": "Nie wykryto baterii",
        "battery_not_detected_hint": "To normalne w komputerze stacjonarnym.",
        "battery_health": "Kondycja",
        "battery_capacity": "Naładowanie",
        "battery_model": "Model",
        "battery_manufacturer": "Producent",
        "battery_technology": "Technologia",
        "battery_cycles": "Cykle ładowania",
        "battery_energy": "Energia",
        "battery_power": "Pobór mocy",
        "battery_time": "Pozostały czas",
        "battery_status": "Stan",
        "charging": "Ładowanie",
        "discharging": "Rozładowywanie",
        "full": "Pełna",
        "not_charging": "Nie ładuje",
        "unknown": "Nieznany",
        "memory": "Pamięć",
        "used_of": "{used} z {total}",
        "disk": "Dysk",
        "network": "Sieć",
        "processes": "Procesy",
        "footer": "↑↓ wybór   Enter otwórz   R rdzenie   C kolory   L język   Q wyjście",
        "footer_process": "↑↓ proces   / szukaj   S sortuj   V kolumny   Backspace zakończ   Esc wróć",
        "footer_search": "Wpisz nazwę   Enter zatwierdź   Esc wyczyść   Backspace usuń znak",
        "footer_confirm": "←→ wybór   Enter zatwierdź   Esc anuluj",
        "footer_cores": "R/Esc wróć   PgUp/PgDn strona   C kolory   L język   Q wyjście",
        "cpu_cores": "RDZENIE PROCESORA",
        "cores_hint": "Bieżące obciążenie i ostatnie pomiary każdego logicznego CPU",
        "memory_hardware_unknown": "Typ RAM niewykryty (opcjonalnie zainstaluj inxi)",
        "page": "strona {current}/{total}",
        "last_samples": "Ostatnie pomiary",
        "current_usage": "Bieżące użycie",
        "used_available_total": "Używane {used} • dostępne {available} • razem {total}",
        "used_free": "/  •  zajęte {used} z {total}  •  wolne {free}",
        "occupied": "{percent:.0f}% zajęte",
        "read": "Odczyt",
        "write": "Zapis",
        "sending": "Wysyłanie",
        "downloading": "↓ pobieranie",
        "uploading": "↑ wysyłanie",
        "sorting": "sortowanie",
        "process": "PROCES",
        "search": "Szukaj",
        "no_processes": "Brak procesów pasujących do wyszukiwania",
        "process_columns": "KOLUMNY PROCESÓW",
        "process_columns_hint": "↑↓ wybór   Spacja włącz/wyłącz   Enter zapisz   Esc anuluj",
        "column_cpu": "Użycie CPU",
        "column_ram": "Użycie RAM",
        "column_gpu": "Użycie GPU",
        "column_energy": "Wpływ energetyczny (szacunek)",
        "energy_short": "ENER.",
        "small_title": "miltop potrzebuje trochę więcej miejsca",
        "terminal": "Terminal",
        "minimum": "Minimum: 72×20",
        "resize": "Powiększ okno lub zmniejsz czcionkę terminala.",
        "exit": "Q — wyjście",
        "kill_title": "ZAKOŃCZENIE PROCESU",
        "kill_question": "Czy zakończyć proces {name} (PID {pid})?",
        "kill_warning": "Proces otrzyma bezpieczny sygnał zakończenia (SIGTERM).",
        "cancel": "Anuluj",
        "terminate": "Zakończ",
        "kill_sent": "Wysłano żądanie zakończenia: {name} (PID {pid})",
        "kill_denied": "Brak uprawnień do zakończenia procesu {pid}",
        "kill_gone": "Proces {pid} już nie działa",
        "kill_protected": "Tego procesu miltop nie może zakończyć",
        "process_mode_hint": "Tryb procesów — wybierz pozycję i użyj Backspace",
        "colors": "Kolory",
        "color_settings": "KOLORY INTERFEJSU",
        "color_hint": "←→/↑↓ wybór   Enter zapisz   Esc anuluj",
        "theme_cyan": "Turkusowy",
        "theme_green": "Zielony",
        "theme_red": "Czerwony",
        "theme_blue": "Niebieski",
        "theme_purple": "Fioletowy",
        "theme_amber": "Bursztynowy",
    },
    "en": {
        "system_manager": "System manager",
        "uptime": "Uptime",
        "refresh": "refresh",
        "components": "COMPONENTS",
        "processor": "Processor",
        "threads": "{count} threads",
        "logical_cpu": "{count} logical CPUs",
        "cpu_topology": "{cores} cores • {threads} threads",
        "load": "load",
        "gpu_usage": "Graphics processor usage",
        "graphics": "Graphics",
        "integrated_gpu": "Integrated",
        "dedicated_gpu": "Dedicated",
        "unknown_gpu": "Unknown type",
        "detected_gpus": "Detected graphics adapters",
        "usage_unavailable": "usage unavailable",
        "temperature": "Temperature",
        "frequency": "Clock",
        "video_memory": "Graphics memory",
        "shared_memory": "shared system memory",
        "driver": "Driver",
        "measurement": "Measurement",
        "battery": "Battery",
        "battery_not_detected": "No battery detected",
        "battery_not_detected_hint": "This is normal on a desktop computer.",
        "battery_health": "Health",
        "battery_capacity": "Charge",
        "battery_model": "Model",
        "battery_manufacturer": "Manufacturer",
        "battery_technology": "Technology",
        "battery_cycles": "Charge cycles",
        "battery_energy": "Energy",
        "battery_power": "Power draw",
        "battery_time": "Time remaining",
        "battery_status": "Status",
        "charging": "Charging",
        "discharging": "Discharging",
        "full": "Full",
        "not_charging": "Not charging",
        "unknown": "Unknown",
        "memory": "Memory",
        "used_of": "{used} of {total}",
        "disk": "Disk",
        "network": "Network",
        "processes": "Processes",
        "footer": "↑↓ select   Enter open   R cores   C colors   L language   Q quit",
        "footer_process": "↑↓ process   / search   S sort   V columns   Backspace end   Esc back",
        "footer_search": "Type a name   Enter apply   Esc clear   Backspace erase",
        "footer_confirm": "←→ select   Enter confirm   Esc cancel",
        "footer_cores": "R/Esc back   PgUp/PgDn page   C colors   L language   Q quit",
        "cpu_cores": "PROCESSOR CORES",
        "cores_hint": "Current load and recent activity for every logical CPU",
        "memory_hardware_unknown": "RAM type not detected (optionally install inxi)",
        "page": "page {current}/{total}",
        "last_samples": "Recent activity",
        "current_usage": "Current usage",
        "used_available_total": "Used {used} • available {available} • total {total}",
        "used_free": "/  •  used {used} of {total}  •  free {free}",
        "occupied": "{percent:.0f}% used",
        "read": "Read",
        "write": "Write",
        "sending": "Sending",
        "downloading": "↓ download",
        "uploading": "↑ upload",
        "sorting": "sorting",
        "process": "PROCESS",
        "search": "Search",
        "no_processes": "No processes match the search",
        "process_columns": "PROCESS COLUMNS",
        "process_columns_hint": "↑↓ select   Space toggle   Enter save   Esc cancel",
        "column_cpu": "CPU usage",
        "column_ram": "RAM usage",
        "column_gpu": "GPU usage",
        "column_energy": "Energy impact (estimate)",
        "energy_short": "ENER.",
        "small_title": "miltop needs a little more room",
        "terminal": "Terminal",
        "minimum": "Minimum: 72×20",
        "resize": "Enlarge the window or reduce the terminal font size.",
        "exit": "Q — quit",
        "kill_title": "END PROCESS",
        "kill_question": "End process {name} (PID {pid})?",
        "kill_warning": "The process will receive a safe termination signal (SIGTERM).",
        "cancel": "Cancel",
        "terminate": "End process",
        "kill_sent": "Termination requested: {name} (PID {pid})",
        "kill_denied": "Permission denied while ending process {pid}",
        "kill_gone": "Process {pid} is no longer running",
        "kill_protected": "miltop cannot end this process",
        "process_mode_hint": "Process mode — select an item and press Backspace",
        "colors": "Colors",
        "color_settings": "INTERFACE COLORS",
        "color_hint": "←→/↑↓ select   Enter save   Esc cancel",
        "theme_cyan": "Cyan",
        "theme_green": "Green",
        "theme_red": "Red",
        "theme_blue": "Blue",
        "theme_purple": "Purple",
        "theme_amber": "Amber",
    },
}


def text(language: str, key: str, **values: Any) -> str:
    template = TEXTS.get(language, TEXTS["pl"]).get(key, key)
    return template.format(**values)


def load_config() -> dict[str, Any]:
    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return config if isinstance(config, dict) else {}
    except (OSError, ValueError, TypeError, AttributeError):
        return {}


def save_config(**values: Any) -> None:
    config = load_config()
    config.update(values)
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = CONFIG_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    temporary.replace(CONFIG_FILE)


def load_language() -> str | None:
    language = load_config().get("language")
    return language if language in TEXTS else None


def save_language(language: str) -> None:
    save_config(language=language)


def load_theme() -> str:
    theme = load_config().get("theme")
    return theme if theme in THEME_NAMES else "cyan"


def save_theme(theme: str) -> None:
    if theme in THEME_NAMES:
        save_config(theme=theme)


def load_process_columns() -> list[str]:
    columns = load_config().get("process_columns")
    if not isinstance(columns, list):
        return list(PROCESS_COLUMN_NAMES)
    return [column for column in PROCESS_COLUMN_NAMES if column in columns]


def save_process_columns(columns: list[str]) -> None:
    save_config(process_columns=[column for column in PROCESS_COLUMN_NAMES if column in columns])


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def human_bytes(value: float, *, rate: bool = False) -> str:
    suffix = "/s" if rate else ""
    units = ("B", "KB", "MB", "GB", "TB")
    value = max(0.0, float(value))
    unit = units[0]
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            break
        value /= 1024.0
    if unit == "B":
        text = f"{value:.0f} {unit}"
    elif value >= 100:
        text = f"{value:.0f} {unit}"
    elif value >= 10:
        text = f"{value:.1f} {unit}"
    else:
        text = f"{value:.2f} {unit}"
    return text + suffix


def human_rate(value: float) -> str:
    return human_bytes(value, rate=True)


def duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, _ = divmod(rest, 60)
    if days:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m"


def sparkline(values: list[float], width: int, ceiling: float | None = None) -> str:
    if width <= 0:
        return ""
    data = values[-width:]
    if len(data) < width:
        data = [0.0] * (width - len(data)) + data
    top = ceiling if ceiling and ceiling > 0 else max(max(data, default=0.0), 1.0)
    chars = []
    for value in data:
        idx = int(round(clamp(value / top, 0.0, 1.0) * (len(BLOCKS) - 1)))
        chars.append(BLOCKS[idx])
    return "".join(chars)


def ellipsize(text: str, width: int) -> str:
    text = str(text).replace("\n", " ")
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width == 1:
        return "…"
    return text[: width - 1] + "…"


@dataclass
class ProcessRow:
    pid: int
    name: str
    cpu: float
    memory: int
    gpu: float = 0.0
    energy: float = 0.0


@dataclass
class GpuDevice:
    card: str
    pci_address: str
    vendor: str
    model: str
    kind: str
    usage_path: Path | None = field(default=None, repr=False)
    temperature_path: Path | None = field(default=None, repr=False)
    frequency_path: Path | None = field(default=None, repr=False)
    frequency_max_path: Path | None = field(default=None, repr=False)
    vram_total_path: Path | None = field(default=None, repr=False)
    vram_used_path: Path | None = field(default=None, repr=False)
    driver: str = ""
    usage: float | None = None
    temperature: float | None = None
    frequency: float | None = None
    frequency_max: float | None = None
    vram_total: int = 0
    vram_used: int = 0
    usage_source: str = ""

    @property
    def name(self) -> str:
        values = [value for value in (self.vendor, self.model) if value]
        return " ".join(values) or self.card.upper()


@dataclass
class BatteryDevice:
    name: str
    manufacturer: str = ""
    model: str = ""
    serial: str = ""
    technology: str = ""
    status: str = "Unknown"
    percent: float = 0.0
    health: float | None = None
    cycles: int | None = None
    energy_now: float | None = None
    energy_full: float | None = None
    energy_design: float | None = None
    power: float | None = None
    voltage: float | None = None
    time_remaining: float | None = None


@dataclass
class Snapshot:
    timestamp: float = 0.0
    cpu: float = 0.0
    per_cpu: list[float] = field(default_factory=list)
    cpu_model: str = ""
    physical_cores: int = 0
    cpu_freq: float = 0.0
    cpu_freq_max: float = 0.0
    temperature: float | None = None
    memory: Any = None
    memory_hardware: str = ""
    memory_model: str = ""
    swap: Any = None
    disk: Any = None
    disk_read_rate: float = 0.0
    disk_write_rate: float = 0.0
    disk_busy: float = 0.0
    net_down: float = 0.0
    net_up: float = 0.0
    process_count: int = 0
    thread_count: int = 0
    load: tuple[float, float, float] = (0.0, 0.0, 0.0)
    uptime: float = 0.0
    processes: list[ProcessRow] = field(default_factory=list)
    gpu_name: str = ""
    gpu_usage: float | None = None
    gpus: list[GpuDevice] = field(default_factory=list)
    batteries: list[BatteryDevice] = field(default_factory=list)


class Sampler:
    def __init__(self, history_size: int = 600, *, background_hardware: bool = True) -> None:
        self.histories: dict[str, deque[float]] = {
            name: deque(maxlen=history_size)
            for name in (
                "cpu",
                "memory",
                "disk",
                "disk_read",
                "disk_write",
                "net_down",
                "net_up",
                "processes",
                "gpu",
                "battery",
            )
        }
        self.previous_time = time.monotonic()
        self.previous_disk = psutil.disk_io_counters()
        self.previous_net = psutil.net_io_counters()
        self.previous_proc_times: dict[int, float] = {}
        self.cached_processes: list[ProcessRow] = []
        self.cached_process_count = 0
        self.cached_thread_count = 0
        self.last_process_sample = 0.0
        self.temperature: float | None = None
        self.temperature_checked = 0.0
        self.core_histories: list[deque[float]] = []
        self.cpu_model = self._read_cpu_model()
        self.physical_cores = int(psutil.cpu_count(logical=False) or 0)
        self.memory_hardware = ""
        self.memory_model = ""
        # Start with fast sysfs identification.  Human-friendly PCI names and
        # optional DIMM data are enriched in one background worker because a
        # cold lspci/inxi call can otherwise delay the first frame by seconds.
        self.gpus = self._find_gpus(with_pci_names=False)
        self.previous_gpu_engines: dict[tuple[int, str, str, str], int] = {}
        self.gpu_usage_checked = 0.0
        self.cached_fdinfo_usage: dict[str, float] = {}
        self.cached_process_gpu_usage: dict[int, float] = {}
        self.cached_nvidia_metrics: dict[str, dict[str, float]] = {}
        self.nvidia_checked = 0.0
        self.cached_batteries: list[BatteryDevice] = []
        self.battery_checked = 0.0
        self._read_fdinfo_gpu_usage(time.monotonic())
        psutil.cpu_percent(interval=None, percpu=True)
        # Detailed DIMM probing is optional and may invoke inxi/lspci.  Start
        # it only after the fast-path hardware setup so it never delays the UI.
        if background_hardware:
            threading.Thread(target=self._load_hardware_details, name="miltop-hardware", daemon=True).start()

    def _load_memory_hardware(self) -> None:
        self.memory_hardware, self.memory_model = self._read_memory_hardware()

    def _load_hardware_details(self) -> None:
        self._load_gpu_names()
        self._load_memory_hardware()

    def _load_gpu_names(self) -> None:
        names = self._pci_gpu_names()
        for gpu in self.gpus:
            vendor, model = names.get(gpu.pci_address, ("", ""))
            if vendor:
                gpu.vendor = vendor
            if model:
                gpu.model = model

    @staticmethod
    def _read_cpu_model() -> str:
        """Read a human-friendly CPU model without starting another process."""
        try:
            for line in Path("/proc/cpuinfo").read_text(errors="replace").splitlines():
                if line.lower().startswith("model name") and ":" in line:
                    return " ".join(line.split(":", 1)[1].split())
        except OSError:
            pass
        return "CPU"

    @staticmethod
    def _read_memory_hardware() -> tuple[str, str]:
        """Best-effort DIMM identification through unprivileged inxi output."""
        try:
            result = subprocess.run(
                ["inxi", "-mxxx", "--no-host", "--no-ssl", "--color", "0"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return "", ""
        if result.returncode != 0:
            return "", ""

        flat = " ".join(result.stdout.split())
        devices = re.split(r"\bDevice-\d+:\s*", flat)[1:]
        if not devices:
            return "", ""

        def values(pattern: str) -> list[str]:
            found: list[str] = []
            for device in devices:
                match = re.search(pattern, device, re.IGNORECASE)
                if match:
                    value = " ".join(match.group(1).split())
                    if value and value not in found:
                        found.append(value)
            return found

        types = values(r"\btype:\s*(\S+)")
        speeds = values(r"\bspeed:\s*([0-9.]+\s*(?:MT/s|MHz))")
        sizes = values(r"\bsize:\s*([0-9.]+\s*(?:[KMGT]i?B))")
        manufacturers = values(r"\bmanufacturer:\s*(.+?)(?=\s+(?:part-no|serial):|$)")
        parts = values(r"\bpart-no:\s*(.+?)(?=\s+serial:|$)")

        hardware: list[str] = []
        if types:
            hardware.append("/".join(types))
        if speeds:
            hardware.append("/".join(speeds))
        if sizes:
            size_text = sizes[0] if len(sizes) == 1 else "+".join(sizes)
            hardware.append(f"{len(devices)}×{size_text}" if len(sizes) == 1 else size_text)

        models: list[str] = []
        for index in range(max(len(manufacturers), len(parts))):
            maker = manufacturers[index] if index < len(manufacturers) else ""
            part = parts[index] if index < len(parts) else ""
            model = " ".join(value for value in (maker, part) if value)
            if model and model not in models:
                models.append(model)
        return " • ".join(hardware), " / ".join(models)

    @staticmethod
    def _pci_gpu_names() -> dict[str, tuple[str, str]]:
        """Return PCI address -> (vendor, model) without administrator access."""
        try:
            result = subprocess.run(
                ["lspci", "-Dmmnn"], capture_output=True, text=True,
                timeout=2, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return {}
        if result.returncode != 0:
            return {}

        devices: dict[str, tuple[str, str]] = {}
        for line in result.stdout.splitlines():
            try:
                fields = shlex.split(line)
            except ValueError:
                continue
            if len(fields) < 4 or not re.search(r"(?:VGA|3D|Display)", fields[1], re.IGNORECASE):
                continue
            clean = lambda value: re.sub(r"\s*\[[0-9a-fA-F]{4}\]$", "", value).strip()
            devices[fields[0]] = (clean(fields[2]), clean(fields[3]))
        return devices

    @staticmethod
    def _gpu_kind(vendor_id: str, model: str, pci_address: str, vram_bytes: int) -> str:
        """Best-effort integrated/dedicated classification from stable hardware facts."""
        model_lower = model.lower()
        if vendor_id == "0x10de":
            return "dedicated"
        if vendor_id == "0x8086":
            if "arc" in model_lower and not pci_address.endswith("00:02.0"):
                return "dedicated"
            return "integrated"
        if vendor_id == "0x1002":
            integrated_markers = ("radeon graphics", "vega", "apu", "ryzen")
            if any(marker in model_lower for marker in integrated_markers):
                return "integrated"
            if vram_bytes >= 1024 ** 3:
                return "dedicated"
        if vram_bytes >= 1024 ** 3:
            return "dedicated"
        return "unknown"

    @classmethod
    def _find_gpus(
        cls,
        drm_root: Path = Path("/sys/class/drm"),
        *,
        with_pci_names: bool = True,
    ) -> list[GpuDevice]:
        pci_names = cls._pci_gpu_names() if with_pci_names else {}
        vendor_names = {
            "0x1002": "AMD",
            "0x8086": "Intel",
            "0x10de": "NVIDIA",
            "0x1a03": "ASPEED",
        }
        devices: list[GpuDevice] = []
        try:
            cards = sorted(
                (path for path in drm_root.iterdir() if re.fullmatch(r"card\d+", path.name)),
                key=lambda path: int(path.name[4:]),
            )
        except OSError:
            return []

        for card in cards:
            device_dir = card / "device"
            try:
                resolved = device_dir.resolve(strict=True)
            except OSError:
                continue
            pci_address = resolved.name

            def read_value(name: str, default: str = "") -> str:
                try:
                    return (device_dir / name).read_text().strip().lower()
                except OSError:
                    return default

            vendor_id = read_value("vendor")
            device_id = read_value("device")
            try:
                vram_bytes = int(read_value("mem_info_vram_total", "0"), 0)
            except ValueError:
                vram_bytes = 0
            pci_vendor, pci_model = pci_names.get(pci_address, ("", ""))
            vendor = pci_vendor or vendor_names.get(vendor_id, vendor_id or "GPU")
            model = pci_model or (f"Device {device_id}" if device_id else card.name.upper())
            usage_path = device_dir / "gpu_busy_percent"

            def first_file(paths: list[Path]) -> Path | None:
                return next((path for path in paths if path.is_file()), None)

            temperature_paths: list[Path] = []
            try:
                temperature_paths.extend(sorted((device_dir / "hwmon").glob("hwmon*/temp1_input")))
            except OSError:
                pass
            try:
                driver = (device_dir / "driver").resolve(strict=True).name
            except OSError:
                driver = ""
            devices.append(GpuDevice(
                card=card.name,
                pci_address=pci_address,
                vendor=vendor,
                model=model,
                kind=cls._gpu_kind(vendor_id, model, pci_address, vram_bytes),
                usage_path=usage_path if usage_path.is_file() else None,
                temperature_path=first_file(temperature_paths),
                frequency_path=first_file([
                    card / "gt_cur_freq_mhz",
                    card / "gt_act_freq_mhz",
                    device_dir / "pp_dpm_sclk",
                ]),
                frequency_max_path=first_file([
                    card / "gt_max_freq_mhz",
                    device_dir / "pp_dpm_sclk",
                ]),
                vram_total_path=first_file([device_dir / "mem_info_vram_total"]),
                vram_used_path=first_file([device_dir / "mem_info_vram_used"]),
                driver=driver,
            ))
        return devices

    @staticmethod
    def _parse_drm_fdinfo(content: str) -> tuple[str, str, dict[str, int]] | None:
        """Parse one Linux DRM fdinfo record into device, client and engine counters."""
        device = ""
        client = ""
        engines: dict[str, int] = {}
        for line in content.splitlines():
            key, separator, value = line.partition(":")
            if not separator:
                continue
            value = value.strip()
            if key == "drm-pdev":
                device = value
            elif key == "drm-client-id":
                client = value
            elif key.startswith("drm-engine-"):
                match = re.match(r"(\d+)\s+ns", value)
                if match:
                    engines[key.removeprefix("drm-engine-")] = int(match.group(1))
        if not device or not client or not engines:
            return None
        return device, client, engines

    def _read_fdinfo_gpu_usage(self, now: float, proc_root: Path = Path("/proc")) -> dict[str, float]:
        """Estimate GPU load from per-client DRM engine time without root access."""
        if now - self.gpu_usage_checked < 0.9:
            return self.cached_fdinfo_usage
        dt = max(0.001, now - self.gpu_usage_checked) if self.gpu_usage_checked else 0.0
        self.gpu_usage_checked = now
        clients: dict[tuple[int, str, str], dict[str, int]] = {}
        try:
            process_dirs = [path for path in proc_root.iterdir() if path.name.isdigit()]
        except OSError:
            return self.cached_fdinfo_usage
        for process_dir in process_dirs:
            try:
                pid = int(process_dir.name)
                descriptors = list((process_dir / "fd").iterdir())
            except (OSError, ValueError):
                continue
            for descriptor in descriptors:
                try:
                    target = os.readlink(descriptor)
                except OSError:
                    continue
                if "/dev/dri/" not in target:
                    continue
                fdinfo = process_dir / "fdinfo" / descriptor.name
                try:
                    parsed = self._parse_drm_fdinfo(fdinfo.read_text(errors="replace"))
                except OSError:
                    continue
                if parsed is None:
                    continue
                device, client, engines = parsed
                key = (pid, client, device)
                existing = clients.setdefault(key, {})
                for engine, counter in engines.items():
                    existing[engine] = max(existing.get(engine, 0), counter)

        current: dict[tuple[int, str, str, str], int] = {}
        deltas: dict[tuple[str, str], int] = {}
        process_deltas: dict[tuple[int, str, str], int] = {}
        for (pid, client, device), engines in clients.items():
            for engine, counter in engines.items():
                key = (pid, client, device, engine)
                current[key] = counter
                previous = self.previous_gpu_engines.get(key)
                if previous is not None and counter >= previous:
                    delta_key = (device, engine)
                    delta = counter - previous
                    deltas[delta_key] = deltas.get(delta_key, 0) + delta
                    process_key = (pid, device, engine)
                    process_deltas[process_key] = process_deltas.get(process_key, 0) + delta
        self.previous_gpu_engines = current
        if dt <= 0:
            self.cached_fdinfo_usage = {}
            self.cached_process_gpu_usage = {}
        else:
            by_device: dict[str, list[float]] = {}
            for (device, _engine), delta in deltas.items():
                by_device.setdefault(device, []).append(delta / (dt * 1_000_000_000) * 100.0)
            self.cached_fdinfo_usage = {
                device: clamp(max(values, default=0.0), 0.0, 100.0)
                for device, values in by_device.items()
            }
            by_process: dict[int, list[float]] = {}
            for (pid, _device, _engine), delta in process_deltas.items():
                by_process.setdefault(pid, []).append(delta / (dt * 1_000_000_000) * 100.0)
            self.cached_process_gpu_usage = {
                pid: clamp(sum(values), 0.0, 100.0)
                for pid, values in by_process.items()
            }
        return self.cached_fdinfo_usage

    @staticmethod
    def _read_number(path: Path | None, scale: float = 1.0) -> float | None:
        if path is None:
            return None
        try:
            content = path.read_text().strip()
            # AMD clock tables mark the current level with an asterisk.
            matches = re.findall(r"([0-9.]+)\s*(?:Mhz|MHz)?", content)
            if not matches:
                return None
            return float(matches[-1] if "*" not in content else next(
                (re.search(r"([0-9.]+)", line).group(1) for line in content.splitlines() if "*" in line and re.search(r"([0-9.]+)", line)),
                matches[-1],
            )) / scale
        except (OSError, ValueError, AttributeError):
            return None

    @staticmethod
    def _read_nvidia_metrics() -> dict[str, dict[str, float]]:
        """Read NVIDIA metrics when the proprietary driver's CLI is available."""
        fields = (
            "pci.bus_id,utilization.gpu,temperature.gpu,memory.used,memory.total,"
            "clocks.current.graphics,clocks.max.graphics"
        )
        try:
            result = subprocess.run(
                ["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return {}
        if result.returncode != 0:
            return {}
        metrics: dict[str, dict[str, float]] = {}
        for line in result.stdout.splitlines():
            values = [value.strip() for value in line.split(",")]
            if len(values) != 7:
                continue
            address_parts = values[0].lower().split(":")
            if len(address_parts) == 3:
                address = f"{address_parts[0][-4:]}:{address_parts[1]}:{address_parts[2]}"
            else:
                address = values[0].lower()
            try:
                metrics[address] = {
                    "usage": float(values[1]), "temperature": float(values[2]),
                    "vram_used": float(values[3]) * 1024 ** 2,
                    "vram_total": float(values[4]) * 1024 ** 2,
                    "frequency": float(values[5]), "frequency_max": float(values[6]),
                }
            except ValueError:
                continue
        return metrics

    def _read_gpus(self, now: float) -> list[GpuDevice]:
        fdinfo_usage = self._read_fdinfo_gpu_usage(now)
        if any(gpu.driver == "nvidia" for gpu in self.gpus) and now - self.nvidia_checked >= 1.0:
            self.cached_nvidia_metrics = self._read_nvidia_metrics()
            self.nvidia_checked = now
        nvidia_metrics = self.cached_nvidia_metrics
        for gpu in self.gpus:
            gpu.usage = None
            gpu.usage_source = ""
            if gpu.usage_path is not None:
                value = self._read_number(gpu.usage_path)
                if value is not None:
                    gpu.usage = clamp(value, 0.0, 100.0)
                    gpu.usage_source = "sysfs"
            elif gpu.pci_address in fdinfo_usage:
                gpu.usage = fdinfo_usage[gpu.pci_address]
                gpu.usage_source = "DRM fdinfo"
            gpu.temperature = self._read_number(gpu.temperature_path, 1000.0)
            gpu.frequency = self._read_number(gpu.frequency_path)
            gpu.frequency_max = self._read_number(gpu.frequency_max_path)
            gpu.vram_total = int(self._read_number(gpu.vram_total_path) or 0)
            gpu.vram_used = int(self._read_number(gpu.vram_used_path) or 0)
            if gpu.pci_address in nvidia_metrics:
                metrics = nvidia_metrics[gpu.pci_address]
                gpu.usage = clamp(metrics["usage"], 0.0, 100.0)
                gpu.temperature = metrics["temperature"]
                gpu.vram_used = int(metrics["vram_used"])
                gpu.vram_total = int(metrics["vram_total"])
                gpu.frequency = metrics["frequency"]
                gpu.frequency_max = metrics["frequency_max"]
                gpu.usage_source = "nvidia-smi"
        return self.gpus

    @staticmethod
    def _read_batteries(power_root: Path = Path("/sys/class/power_supply")) -> list[BatteryDevice]:
        """Read laptop battery identity and live health data from Linux power_supply."""
        batteries: list[BatteryDevice] = []
        try:
            supplies = sorted(power_root.iterdir())
        except OSError:
            return batteries

        for supply in supplies:
            def value(name: str, default: str = "") -> str:
                try:
                    return (supply / name).read_text().strip()
                except OSError:
                    return default

            if value("type").lower() != "battery" or value("present", "1") == "0":
                continue

            def number(name: str) -> float | None:
                try:
                    return float(value(name))
                except ValueError:
                    return None

            voltage_uv = number("voltage_now") or number("voltage_min_design")
            energy_now_raw = number("energy_now")
            energy_full_raw = number("energy_full")
            energy_design_raw = number("energy_full_design")
            power_raw = number("power_now")
            charge_now = number("charge_now")
            charge_full = number("charge_full")
            charge_design = number("charge_full_design")
            current_now = number("current_now")

            def energy_wh(energy: float | None, charge: float | None) -> float | None:
                if energy is not None:
                    return energy / 1_000_000.0
                if charge is not None and voltage_uv is not None:
                    return charge * voltage_uv / 1_000_000_000_000.0
                return None

            energy_now = energy_wh(energy_now_raw, charge_now)
            energy_full = energy_wh(energy_full_raw, charge_full)
            energy_design = energy_wh(energy_design_raw, charge_design)
            if power_raw is not None:
                power = power_raw / 1_000_000.0
            elif current_now is not None and voltage_uv is not None:
                power = current_now * voltage_uv / 1_000_000_000_000.0
            else:
                power = None
            health = None
            if energy_full and energy_design:
                health = clamp(energy_full / energy_design * 100.0, 0.0, 150.0)
            remaining = None
            status = value("status", "Unknown")
            if power and power > 0:
                if status.lower() == "charging" and energy_full is not None and energy_now is not None:
                    remaining = max(0.0, energy_full - energy_now) / power * 3600.0
                elif energy_now is not None:
                    remaining = energy_now / power * 3600.0
            try:
                cycles = int(value("cycle_count"))
            except ValueError:
                cycles = None
            try:
                percent = clamp(float(value("capacity", "0")), 0.0, 100.0)
            except ValueError:
                percent = 0.0
            batteries.append(BatteryDevice(
                name=supply.name,
                manufacturer=value("manufacturer"),
                model=value("model_name"),
                serial=value("serial_number"),
                technology=value("technology"),
                status=status,
                percent=percent,
                health=health,
                cycles=cycles,
                energy_now=energy_now,
                energy_full=energy_full,
                energy_design=energy_design,
                power=power,
                voltage=voltage_uv / 1_000_000.0 if voltage_uv is not None else None,
                time_remaining=remaining,
            ))
        return batteries

    def _read_temperature(self, now: float) -> float | None:
        if now - self.temperature_checked < 4.0:
            return self.temperature
        self.temperature_checked = now
        try:
            groups = psutil.sensors_temperatures(fahrenheit=False)
            preferred = ("coretemp", "k10temp", "cpu_thermal", "acpitz")
            entries = next((groups[key] for key in preferred if groups.get(key)), [])
            if not entries:
                entries = [entry for values in groups.values() for entry in values]
            valid = [entry.current for entry in entries if 0 < entry.current < 130]
            self.temperature = max(valid) if valid else None
        except (AttributeError, OSError):
            self.temperature = None
        return self.temperature

    def _processes(self, dt: float) -> tuple[list[ProcessRow], int, int]:
        rows: list[ProcessRow] = []
        current_times: dict[int, float] = {}
        threads = 0
        for proc in psutil.process_iter(("pid", "name", "memory_info", "cpu_times", "num_threads")):
            try:
                info = proc.info
                times = info["cpu_times"]
                total_time = float(times.user + times.system)
                pid = int(info["pid"])
                old_time = self.previous_proc_times.get(pid, total_time)
                cpu = max(0.0, (total_time - old_time) / max(dt, 0.001) * 100.0)
                current_times[pid] = total_time
                threads += int(info.get("num_threads") or 0)
                rows.append(
                    ProcessRow(
                        pid=pid,
                        name=info.get("name") or "?",
                        cpu=cpu,
                        memory=int(info["memory_info"].rss),
                        gpu=self.cached_process_gpu_usage.get(pid, 0.0),
                    )
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError, TypeError):
                continue
        self.previous_proc_times = current_times
        return rows, len(rows), threads

    def sample(self) -> Snapshot:
        now = time.monotonic()
        dt = max(0.001, now - self.previous_time)
        self.previous_time = now

        per_cpu = psutil.cpu_percent(interval=None, percpu=True)
        cpu = sum(per_cpu) / len(per_cpu) if per_cpu else 0.0
        while len(self.core_histories) < len(per_cpu):
            self.core_histories.append(deque(maxlen=120))
        if len(self.core_histories) > len(per_cpu):
            self.core_histories = self.core_histories[: len(per_cpu)]
        for index, value in enumerate(per_cpu):
            self.core_histories[index].append(float(value))
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage("/")
        disk_now = psutil.disk_io_counters()
        net_now = psutil.net_io_counters()

        disk_read = disk_write = disk_busy = 0.0
        if disk_now is not None and self.previous_disk is not None:
            disk_read = max(0.0, (disk_now.read_bytes - self.previous_disk.read_bytes) / dt)
            disk_write = max(0.0, (disk_now.write_bytes - self.previous_disk.write_bytes) / dt)
            if hasattr(disk_now, "busy_time"):
                disk_busy = clamp((disk_now.busy_time - self.previous_disk.busy_time) / (dt * 10.0), 0.0, 100.0)
        self.previous_disk = disk_now

        net_down = net_up = 0.0
        if net_now is not None and self.previous_net is not None:
            net_down = max(0.0, (net_now.bytes_recv - self.previous_net.bytes_recv) / dt)
            net_up = max(0.0, (net_now.bytes_sent - self.previous_net.bytes_sent) / dt)
        self.previous_net = net_now

        freq = psutil.cpu_freq()
        gpus = self._read_gpus(now)
        gpu_values = [device.usage for device in gpus if device.usage is not None]
        gpu = max(gpu_values) if gpu_values else None
        primary_gpu = gpus[0] if gpus else None

        # Enumerating every /proc entry is the most expensive part of a task
        # manager.  Hardware graphs stay live every tick, while the process
        # table refreshes every two seconds - visually immediate, much lighter.
        process_dt = now - self.last_process_sample if self.last_process_sample else dt
        if not self.cached_processes or process_dt >= 2.0:
            self.cached_processes, self.cached_process_count, self.cached_thread_count = self._processes(process_dt)
            self.last_process_sample = now
        processes = self.cached_processes
        for process in processes:
            process.gpu = self.cached_process_gpu_usage.get(process.pid, 0.0)
            # Linux does not expose reliable per-process watts.  This bounded
            # activity score is intentionally labelled as an energy impact.
            process.energy = clamp(process.cpu * 0.65 + process.gpu * 0.35, 0.0, 100.0)
        process_count = self.cached_process_count
        thread_count = self.cached_thread_count
        if now - self.battery_checked >= 1.0:
            self.cached_batteries = self._read_batteries()
            self.battery_checked = now
        batteries = self.cached_batteries

        snap = Snapshot(
            timestamp=time.time(),
            cpu=cpu,
            per_cpu=per_cpu,
            cpu_model=self.cpu_model,
            physical_cores=self.physical_cores,
            cpu_freq=float(freq.current if freq else 0.0),
            cpu_freq_max=float(freq.max if freq else 0.0),
            temperature=self._read_temperature(now),
            memory=memory,
            memory_hardware=self.memory_hardware,
            memory_model=self.memory_model,
            swap=swap,
            disk=disk,
            disk_read_rate=disk_read,
            disk_write_rate=disk_write,
            disk_busy=disk_busy,
            net_down=net_down,
            net_up=net_up,
            process_count=process_count,
            thread_count=thread_count,
            load=os.getloadavg(),
            uptime=time.time() - psutil.boot_time(),
            processes=processes,
            gpu_name=primary_gpu.name if primary_gpu else "",
            gpu_usage=gpu,
            gpus=gpus,
            batteries=batteries,
        )

        values = {
            "cpu": cpu,
            "memory": memory.percent,
            "disk": disk_busy,
            "disk_read": disk_read,
            "disk_write": disk_write,
            "net_down": net_down,
            "net_up": net_up,
            "processes": float(process_count),
            "gpu": gpu or 0.0,
            "battery": batteries[0].percent if batteries else 0.0,
        }
        for key, value in values.items():
            self.histories[key].append(float(value))
        return snap


class Theme:
    TEXT = 1
    MUTED = 2
    ACCENT = 3
    SELECTED = 4
    GOOD = 5
    WARN = 6
    BAD = 7
    BORDER = 8
    SECONDARY = 9

    SWATCH = 20
    PALETTES = {
        "cyan": (81, 24, 177),
        "green": (114, 22, 81),
        "red": (203, 52, 221),
        "blue": (75, 25, 81),
        "purple": (177, 54, 81),
        "amber": (221, 58, 203),
    }
    BASIC = {
        "cyan": curses.COLOR_CYAN,
        "green": curses.COLOR_GREEN,
        "red": curses.COLOR_RED,
        "blue": curses.COLOR_BLUE,
        "purple": curses.COLOR_MAGENTA,
        "amber": curses.COLOR_YELLOW,
    }

    @staticmethod
    def init(enabled: bool, theme: str = "cyan") -> None:
        if not enabled or not curses.has_colors():
            return
        curses.start_color()
        curses.use_default_colors()
        accent, selected_bg, secondary = Theme.PALETTES.get(theme, Theme.PALETTES["cyan"])
        if curses.COLORS >= 256:
            definitions = {
                Theme.TEXT: (252, -1),
                Theme.MUTED: (244, -1),
                Theme.ACCENT: (accent, -1),
                Theme.SELECTED: (255, selected_bg),
                Theme.GOOD: (114, -1),
                Theme.WARN: (221, -1),
                Theme.BAD: (203, -1),
                Theme.BORDER: (240, -1),
                Theme.SECONDARY: (secondary, -1),
            }
        else:
            basic = Theme.BASIC.get(theme, curses.COLOR_CYAN)
            definitions = {
                Theme.TEXT: (curses.COLOR_WHITE, -1),
                Theme.MUTED: (curses.COLOR_WHITE, -1),
                Theme.ACCENT: (basic, -1),
                Theme.SELECTED: (curses.COLOR_BLACK, basic),
                Theme.GOOD: (curses.COLOR_GREEN, -1),
                Theme.WARN: (curses.COLOR_YELLOW, -1),
                Theme.BAD: (curses.COLOR_RED, -1),
                Theme.BORDER: (curses.COLOR_WHITE, -1),
                Theme.SECONDARY: (basic, -1),
            }
        for pair, (fg, bg) in definitions.items():
            try:
                curses.init_pair(pair, fg, bg)
            except curses.error:
                pass
        for index, name in enumerate(THEME_NAMES):
            color = Theme.PALETTES[name][0] if curses.COLORS >= 256 else Theme.BASIC[name]
            try:
                curses.init_pair(Theme.SWATCH + index, color, -1)
            except curses.error:
                pass


def choose_language(screen: Any, color: bool, current: str = "pl", theme: str = "cyan") -> str:
    """Show the first-run language screen and persist the selection."""
    options = [("pl", "Polski"), ("en", "English")]
    selected = next((index for index, item in enumerate(options) if item[0] == current), 0)
    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()
    screen.keypad(True)
    screen.timeout(-1)
    Theme.init(color, theme)

    while True:
        screen.erase()
        height, width = screen.getmaxyx()
        logo_width = max(len(line) for line in LOGO)
        logo_y = max(1, height // 2 - 8)
        if width >= logo_width + 2 and height >= 17:
            for offset, line in enumerate(LOGO):
                try:
                    screen.addnstr(logo_y + offset, max(0, (width - len(line)) // 2), line, width, curses.color_pair(Theme.ACCENT) | curses.A_BOLD)
                except curses.error:
                    pass
            subtitle = "SYSTEM MONITOR  •  MENEDŻER SYSTEMU"
            prompt_y = logo_y + len(LOGO) + 2
        else:
            title = "◆  MILTOP  ◆"
            try:
                screen.addnstr(2, max(0, (width - len(title)) // 2), title, width, curses.color_pair(Theme.ACCENT) | curses.A_BOLD)
            except curses.error:
                pass
            subtitle = "SYSTEM MONITOR / MENEDŻER SYSTEMU"
            prompt_y = 5

        for row, value, pair in (
            (prompt_y - 1, subtitle, Theme.MUTED),
            (prompt_y + 1, "Wybierz język  /  Choose language", Theme.TEXT),
        ):
            try:
                screen.addnstr(row, max(0, (width - len(value)) // 2), value, max(0, width - 1), curses.color_pair(pair) | curses.A_BOLD)
            except curses.error:
                pass

        option_y = prompt_y + 4
        option_width = 18
        total_width = option_width * 2 + 3
        start_x = max(0, (width - total_width) // 2)
        for index, (_, label) in enumerate(options):
            x = start_x + index * (option_width + 3)
            attr = curses.color_pair(Theme.SELECTED) | curses.A_BOLD if index == selected else curses.color_pair(Theme.BORDER)
            value = f"  {label:^{option_width - 4}}  "
            try:
                screen.addnstr(option_y, x, value, max(0, min(option_width, width - x)), attr)
            except curses.error:
                pass
        hint = "← →  wybór / select     Enter  zatwierdź / confirm"
        try:
            screen.addnstr(min(height - 2, option_y + 3), max(0, (width - len(hint)) // 2), hint, max(0, width - 1), curses.color_pair(Theme.MUTED))
        except curses.error:
            pass
        screen.refresh()

        key = screen.getch()
        if key in (curses.KEY_LEFT, curses.KEY_UP, ord("h"), ord("k")):
            selected = (selected - 1) % len(options)
        elif key in (curses.KEY_RIGHT, curses.KEY_DOWN, ord("l"), ord("j"), 9):
            selected = (selected + 1) % len(options)
        elif key in (10, 13, curses.KEY_ENTER):
            language = options[selected][0]
            save_language(language)
            return language
        elif key in (ord("p"), ord("P")):
            save_language("pl")
            return "pl"
        elif key in (ord("e"), ord("E")):
            save_language("en")
            return "en"


def choose_theme(screen: Any, color: bool, language: str, current: str) -> str:
    """Full-screen, keyboard-friendly palette chooser with color swatches."""
    selected = THEME_NAMES.index(current) if current in THEME_NAMES else 0
    original = current if current in THEME_NAMES else "cyan"
    screen.timeout(-1)

    while True:
        Theme.init(color, THEME_NAMES[selected])
        screen.erase()
        height, width = screen.getmaxyx()
        title = text(language, "color_settings")
        screen.addnstr(2, max(1, (width - len(title)) // 2), title, max(1, width - 2), curses.color_pair(Theme.ACCENT) | curses.A_BOLD)
        subtitle = "miltop  •  " + text(language, "colors")
        screen.addnstr(4, max(1, (width - len(subtitle)) // 2), subtitle, max(1, width - 2), curses.color_pair(Theme.MUTED))

        columns = 2 if width >= 62 else 1
        card_width = min(28, max(20, (width - 8) // columns))
        start_x = max(1, (width - (card_width * columns + 3 * (columns - 1))) // 2)
        start_y = 7
        for index, name in enumerate(THEME_NAMES):
            row, column = divmod(index, columns)
            y = start_y + row * 3
            x = start_x + column * (card_width + 3)
            label = text(language, "theme_" + name)
            marker = "●  ■"
            active = index == selected
            attr = curses.color_pair(Theme.SELECTED) | curses.A_BOLD if active else curses.color_pair(Theme.BORDER)
            swatch = curses.color_pair(Theme.SWATCH + index) | curses.A_BOLD
            try:
                screen.addnstr(y, x, " " * card_width, card_width, attr)
                screen.addnstr(y, x + 2, marker, 4, attr if active else swatch)
                screen.addnstr(y, x + 8, label, max(1, card_width - 10), attr)
            except curses.error:
                pass

        hint = text(language, "color_hint")
        try:
            screen.addnstr(min(height - 2, start_y + 10), max(1, (width - len(hint)) // 2), hint, max(1, width - 2), curses.color_pair(Theme.MUTED))
        except curses.error:
            pass
        screen.refresh()

        key = screen.getch()
        if key in (curses.KEY_LEFT, ord("h"), ord("H")):
            selected = (selected - 1) % len(THEME_NAMES)
        elif key in (curses.KEY_RIGHT, ord("l")):
            selected = (selected + 1) % len(THEME_NAMES)
        elif key in (curses.KEY_UP, ord("k"), ord("K")):
            selected = (selected - columns) % len(THEME_NAMES)
        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            selected = (selected + columns) % len(THEME_NAMES)
        elif key in (10, 13, curses.KEY_ENTER):
            chosen = THEME_NAMES[selected]
            save_theme(chosen)
            return chosen
        elif key == 27:
            Theme.init(color, original)
            return original


def choose_process_columns(screen: Any, color: bool, language: str, current: list[str], theme: str) -> list[str]:
    """Let users persistently choose optional columns in the process table."""
    original = [column for column in PROCESS_COLUMN_NAMES if column in current]
    enabled = set(original)
    selected = 0
    screen.timeout(-1)
    Theme.init(color, theme)
    while True:
        screen.erase()
        height, width = screen.getmaxyx()
        title = text(language, "process_columns")
        hint = text(language, "process_columns_hint")
        start_y = max(2, (height - len(PROCESS_COLUMN_NAMES) * 3 - 5) // 2)
        panel_width = min(max(44, len(hint) + 4), max(20, width - 4))
        start_x = max(1, (width - panel_width) // 2)
        try:
            screen.addnstr(start_y, max(1, (width - len(title)) // 2), title, width - 2, curses.color_pair(Theme.ACCENT) | curses.A_BOLD)
        except curses.error:
            pass
        for index, column in enumerate(PROCESS_COLUMN_NAMES):
            row = start_y + 2 + index * 2
            checked = column in enabled
            marker = "●" if checked else "○"
            label = text(language, f"column_{column}")
            value = f" {marker}  {label}"
            attr = curses.color_pair(Theme.SELECTED) | curses.A_BOLD if index == selected else curses.color_pair(Theme.TEXT if checked else Theme.MUTED)
            try:
                screen.addnstr(row, start_x, value.ljust(panel_width), panel_width, attr)
            except curses.error:
                pass
        try:
            screen.addnstr(start_y + 2 + len(PROCESS_COLUMN_NAMES) * 2, max(1, (width - len(hint)) // 2), hint, width - 2, curses.color_pair(Theme.MUTED))
        except curses.error:
            pass
        screen.refresh()
        key = screen.getch()
        if key in (curses.KEY_UP, ord("k"), ord("K")):
            selected = (selected - 1) % len(PROCESS_COLUMN_NAMES)
        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            selected = (selected + 1) % len(PROCESS_COLUMN_NAMES)
        elif key == ord(" "):
            column = PROCESS_COLUMN_NAMES[selected]
            if column in enabled:
                enabled.remove(column)
            else:
                enabled.add(column)
        elif key in (10, 13, curses.KEY_ENTER):
            chosen = [column for column in PROCESS_COLUMN_NAMES if column in enabled]
            save_process_columns(chosen)
            return chosen
        elif key == 27:
            return original


class MiltopApp:
    def __init__(self, screen: Any, interval: float, color: bool = True, language: str = "pl", theme: str = "cyan") -> None:
        self.screen = screen
        self.interval = clamp(interval, 0.25, 5.0)
        self.sampler = Sampler()
        self.snapshot = self.sampler.sample()
        self.selected = 0
        self.running = True
        self.color = color
        self.language = language if language in TEXTS else "pl"
        self.theme = theme if theme in THEME_NAMES else "cyan"
        self.last_sample = time.monotonic()
        self.sort_mode = "cpu"
        self.process_columns = load_process_columns()
        self.process_mode = False
        self.cores_mode = False
        self.core_page = 0
        self.process_index = 0
        self.process_offset = 0
        self.search_active = False
        self.search_query = ""
        self.confirm_process: ProcessRow | None = None
        self.confirm_choice = 0
        self.status_message = ""
        self.status_until = 0.0
        self.tile_regions: list[tuple[int, int, int, int, int]] = []
        self.process_header_regions: dict[str, tuple[int, int, int, int]] = {}
        self.process_row_regions: list[tuple[int, int, int, int, int]] = []
        self._configure_terminal()

    def t(self, key: str, **values: Any) -> str:
        return text(self.language, key, **values)

    def _configure_terminal(self) -> None:
        locale.setlocale(locale.LC_ALL, "")
        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(True)
        self.screen.timeout(100)
        Theme.init(self.color, self.theme)
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        except curses.error:
            pass

    @property
    def components(self) -> list[str]:
        items = ["cpu", "memory", "disk", "network", "battery", "processes"]
        if self.snapshot.gpus:
            items.insert(1, "gpu")
        return items

    def attr(self, pair: int, extra: int = 0) -> int:
        base = curses.color_pair(pair) if self.color and curses.has_colors() else 0
        return base | extra

    def add(self, y: int, x: int, text: str, attr: int = 0, width: int | None = None) -> None:
        height, screen_width = self.screen.getmaxyx()
        if y < 0 or y >= height or x < 0 or x >= screen_width:
            return
        available = screen_width - x
        if width is not None:
            available = min(available, max(0, width))
        if available <= 0:
            return
        try:
            self.screen.addnstr(y, x, str(text), available, attr)
        except curses.error:
            pass

    def line(self, y: int, x: int, width: int, char: str = "─", attr: int = 0) -> None:
        self.add(y, x, char * max(0, width), attr, width)

    def box(self, y: int, x: int, height: int, width: int, attr: int = 0) -> None:
        if height < 2 or width < 2:
            return
        self.add(y, x, "╭" + "─" * (width - 2) + "╮", attr, width)
        for row in range(1, height - 1):
            self.add(y + row, x, "│", attr)
            self.add(y + row, x + width - 1, "│", attr)
        self.add(y + height - 1, x, "╰" + "─" * (width - 2) + "╯", attr, width)

    def fill(self, y: int, x: int, height: int, width: int, attr: int) -> None:
        for row in range(max(0, height)):
            self.add(y + row, x, " " * max(0, width), attr, width)

    def metric_color(self, value: float) -> int:
        if value >= 90:
            return Theme.BAD
        if value >= 72:
            return Theme.WARN
        return Theme.ACCENT

    def tile_data(self, component: str) -> tuple[str, str, str, list[float], float | None]:
        s = self.snapshot
        h = self.sampler.histories
        if component == "cpu":
            detail = s.cpu_model or self.t("logical_cpu", count=len(s.per_cpu))
            return self.t("processor"), f"{s.cpu:.0f}%", detail, list(h["cpu"]), 100.0
        if component == "gpu":
            primary = s.gpus[0]
            value = f"{s.gpu_usage:.0f}%" if s.gpu_usage is not None else str(len(s.gpus))
            detail = f"{self.t(primary.kind + '_gpu')} • {primary.name}"
            return self.t("graphics"), value, detail, list(h["gpu"]), 100.0
        if component == "memory":
            hardware = s.memory_hardware or self.t("memory_hardware_unknown")
            detail = f"{hardware} • {human_bytes(s.memory.used)} / {human_bytes(s.memory.total)}"
            return self.t("memory"), f"{s.memory.percent:.0f}%", detail, list(h["memory"]), 100.0
        if component == "disk":
            return self.t("disk"), f"{s.disk.percent:.0f}%", f"R {human_rate(s.disk_read_rate)}  W {human_rate(s.disk_write_rate)}", list(h["disk"]), 100.0
        if component == "network":
            return self.t("network"), human_rate(s.net_down), f"↓ {human_rate(s.net_down)}  ↑ {human_rate(s.net_up)}", list(h["net_down"]), None
        if component == "battery":
            if not s.batteries:
                return self.t("battery"), "—", self.t("battery_not_detected"), list(h["battery"]), 100.0
            battery = s.batteries[0]
            detail = " • ".join(value for value in (battery.manufacturer, battery.model) if value)
            return self.t("battery"), f"{battery.percent:.0f}%", detail or battery.name, list(h["battery"]), 100.0
        return self.t("processes"), str(s.process_count), self.t("threads", count=s.thread_count), list(h["processes"]), None

    def draw_header(self, width: int) -> None:
        self.add(0, 2, "miltop", self.attr(Theme.ACCENT, curses.A_BOLD))
        self.add(0, 9, self.t("system_manager"), self.attr(Theme.MUTED))
        right = f"{self.t('uptime')} {duration(self.snapshot.uptime)}  •  {self.t('refresh')} {self.interval:g}s"
        self.add(0, max(2, width - len(right) - 2), right, self.attr(Theme.MUTED))
        self.line(1, 0, width, "─", self.attr(Theme.BORDER))

    def draw_footer(self, height: int, width: int) -> None:
        self.line(height - 2, 0, width, "─", self.attr(Theme.BORDER))
        if self.confirm_process is not None:
            help_text = self.t("footer_confirm")
        elif self.cores_mode:
            help_text = self.t("footer_cores")
        elif self.process_mode:
            help_text = self.t("footer_search") if self.search_active else self.t("footer_process")
        else:
            help_text = self.t("footer")
        self.add(height - 1, 2, ellipsize(help_text, width - 4), self.attr(Theme.MUTED))

    def draw_sidebar(self, y: int, x: int, height: int, width: int) -> None:
        self.add(y, x + 1, self.t("components"), self.attr(Theme.MUTED, curses.A_BOLD))
        components = self.components
        self.selected = min(self.selected, len(components) - 1)
        available = height - 2
        tile_h = 4 if available >= len(components) * 4 else 3
        visible_tiles = max(1, available // tile_h)
        first = int(clamp(self.selected - visible_tiles // 2, 0, max(0, len(components) - visible_tiles)))
        self.tile_regions = []
        for visible_index, index in enumerate(range(first, min(len(components), first + visible_tiles))):
            component = components[index]
            tile_y = y + 2 + visible_index * tile_h
            if tile_y + tile_h > y + height:
                break
            selected = index == self.selected
            background = self.attr(Theme.SELECTED) if selected else 0
            border = background if selected else self.attr(Theme.BORDER)
            if selected:
                self.fill(tile_y, x, tile_h, width, background)
            self.box(tile_y, x, tile_h, width, border)
            title, value, detail, history, ceiling = self.tile_data(component)
            title_attr = background | curses.A_BOLD if selected else self.attr(Theme.TEXT, curses.A_BOLD)
            value_attr = background | curses.A_BOLD if selected else self.attr(Theme.ACCENT, curses.A_BOLD)
            self.add(tile_y + 1, x + 2, ellipsize(title, max(1, width - len(value) - 6)), title_attr)
            self.add(tile_y + 1, x + width - len(value) - 2, value, value_attr)
            if tile_h >= 4:
                self.add(tile_y + 2, x + 2, ellipsize(detail, width - 4), background if selected else self.attr(Theme.MUTED))
            else:
                graph_w = max(0, width - len(title) - len(value) - 7)
                self.add(tile_y + 1, x + len(title) + 3, sparkline(history, graph_w, ceiling), background if selected else self.attr(Theme.ACCENT))
            self.tile_regions.append((tile_y, x, tile_h, width, index))

    def draw_percent_bar(self, y: int, x: int, width: int, value: float, color: int | None = None) -> None:
        width = max(1, width)
        filled = int(round(width * clamp(value, 0.0, 100.0) / 100.0))
        pair = color or self.metric_color(value)
        self.add(y, x, "█" * filled, self.attr(pair), width)
        self.add(y, x + filled, "░" * (width - filled), self.attr(Theme.BORDER), width - filled)

    def draw_chart(
        self,
        y: int,
        x: int,
        height: int,
        width: int,
        primary: list[float],
        secondary: list[float] | None = None,
        ceiling: float | None = None,
        primary_color: int = Theme.ACCENT,
        secondary_color: int = Theme.SECONDARY,
    ) -> float:
        height = max(3, height)
        width = max(4, width)
        p = primary[-width:]
        s = (secondary or [])[-width:]
        max_value = ceiling or max(max(p, default=0.0), max(s, default=0.0), 1.0)
        if ceiling is None:
            magnitude = 10 ** math.floor(math.log10(max_value)) if max_value > 0 else 1
            max_value = max(magnitude, math.ceil(max_value / magnitude) * magnitude)
        p = [0.0] * (width - len(p)) + p
        s = [0.0] * (width - len(s)) + s
        for row in range(height):
            threshold_high = max_value * (height - row) / height
            threshold_low = max_value * (height - row - 1) / height
            chars = []
            attrs: list[int] = []
            for col in range(width):
                pv = p[col]
                sv = s[col] if s else 0.0
                value = max(pv, sv)
                if value <= threshold_low:
                    chars.append("·" if row in (height // 2, height - 1) else " ")
                    attrs.append(self.attr(Theme.BORDER))
                    continue
                fraction = clamp((value - threshold_low) / max(threshold_high - threshold_low, 0.001), 0.0, 1.0)
                chars.append(BLOCKS[max(1, int(round(fraction * 8)))])
                attrs.append(self.attr(primary_color if pv >= sv else secondary_color))
            # Group equal attributes to avoid one curses call per cell.
            start = 0
            while start < width:
                end = start + 1
                while end < width and attrs[end] == attrs[start]:
                    end += 1
                self.add(y + row, x + start, "".join(chars[start:end]), attrs[start], end - start)
                start = end
        return max_value

    def sorted_processes(self, sort_mode: str | None = None) -> list[ProcessRow]:
        mode = sort_mode or self.sort_mode
        rows = self.snapshot.processes
        query = self.search_query.strip().casefold()
        if query:
            rows = [proc for proc in rows if query in proc.name.casefold() or query in str(proc.pid)]
        if mode == "name":
            return sorted(rows, key=lambda proc: (proc.name.casefold(), proc.pid))
        keys = {
            "ram": lambda proc: proc.memory,
            "gpu": lambda proc: proc.gpu,
            "energy": lambda proc: proc.energy,
        }
        key = keys.get(mode, lambda proc: proc.cpu)
        return sorted(rows, key=key, reverse=True)

    def draw_process_table(
        self,
        y: int,
        x: int,
        height: int,
        width: int,
        memory_sort: bool = False,
        interactive: bool = False,
        sort_mode: str | None = None,
    ) -> None:
        if height < 3:
            return

        mode = sort_mode or ("ram" if memory_sort else "cpu")
        rows = self.sorted_processes(mode)
        visible_count = max(1, height - 2)
        if interactive and rows:
            self.process_index = int(clamp(self.process_index, 0, len(rows) - 1))
            if self.process_index < self.process_offset:
                self.process_offset = self.process_index
            elif self.process_index >= self.process_offset + visible_count:
                self.process_offset = self.process_index - visible_count + 1
            self.process_offset = int(clamp(self.process_offset, 0, max(0, len(rows) - visible_count)))
            shown = rows[self.process_offset : self.process_offset + visible_count]
        else:
            shown = rows[:visible_count]
        column_widths = {"cpu": 6, "ram": 8, "gpu": 6, "energy": 7}
        enabled_columns = [column for column in PROCESS_COLUMN_NAMES if column in self.process_columns]
        while enabled_columns and width - 8 - sum(column_widths[column] for column in enabled_columns) < 8:
            enabled_columns.pop()
        name_width = max(8, width - 8 - sum(column_widths[column] for column in enabled_columns))
        self.process_header_regions = {}
        self.process_row_regions = []
        self.add(y, x, "PID", self.attr(Theme.MUTED, curses.A_BOLD), 7)
        name_label = self.t("process") + (" ↑" if mode == "name" else "")
        self.add(y, x + 8, name_label, self.attr(Theme.ACCENT if mode == "name" else Theme.MUTED, curses.A_BOLD), name_width)
        column_x: dict[str, int] = {}
        next_x = x + 8 + name_width
        labels = {"cpu": "CPU", "ram": "RAM", "gpu": "GPU", "energy": self.t("energy_short")}
        for column in enabled_columns:
            column_x[column] = next_x
            label = labels[column] + (" ↓" if mode == column else "")
            self.add(y, next_x, label, self.attr(Theme.ACCENT if mode == column else Theme.MUTED, curses.A_BOLD), column_widths[column])
            next_x += column_widths[column]
        if interactive:
            self.process_header_regions = {"name": (y, x + 8, 1, name_width)}
            self.process_header_regions.update({
                column: (y, column_x[column], 1, column_widths[column]) for column in enabled_columns
            })
        self.line(y + 1, x, width, "─", self.attr(Theme.BORDER))
        if not shown and self.search_query:
            self.add(y + 3, x, self.t("no_processes"), self.attr(Theme.MUTED), width)
        for index, proc in enumerate(shown):
            row_y = y + 2 + index
            actual_index = self.process_offset + index if interactive else index
            selected = interactive and actual_index == self.process_index
            row_attr = self.attr(Theme.SELECTED) if selected else 0
            if selected:
                self.fill(row_y, x, 1, width, row_attr)
            self.add(row_y, x, str(proc.pid), row_attr or self.attr(Theme.MUTED), 7)
            self.add(row_y, x + 8, ellipsize(proc.name, name_width - 1), row_attr or self.attr(Theme.TEXT), name_width)
            values = {
                "cpu": f"{proc.cpu:4.0f}%",
                "ram": human_bytes(proc.memory).replace(" ", ""),
                "gpu": f"{proc.gpu:4.0f}%",
                "energy": f"{proc.energy:4.0f}%",
            }
            for column in enabled_columns:
                metric = proc.memory if column == "ram" else getattr(proc, column)
                pair = Theme.TEXT if column == "ram" else self.metric_color(min(float(metric), 100.0))
                self.add(row_y, column_x[column], values[column], row_attr or self.attr(pair), column_widths[column])
            if interactive:
                self.process_row_regions.append((row_y, x, 1, width, actual_index))

    def draw_detail_header(self, y: int, x: int, width: int, title: str, value: str, subtitle: str) -> None:
        self.add(y, x, title, self.attr(Theme.TEXT, curses.A_BOLD), width)
        self.add(y + 1, x, value, self.attr(Theme.ACCENT, curses.A_BOLD), width)
        self.add(y + 2, x, ellipsize(subtitle, width), self.attr(Theme.MUTED), width)

    def draw_cpu(self, y: int, x: int, height: int, width: int) -> None:
        s = self.snapshot
        temp = f" • {s.temperature:.0f}°C" if s.temperature is not None else ""
        topology = self.t("cpu_topology", cores=s.physical_cores or len(s.per_cpu), threads=len(s.per_cpu))
        frequency = f"{s.cpu_freq / 1000:.2f} GHz"
        if s.cpu_freq_max:
            frequency += f" / {s.cpu_freq_max / 1000:.2f} GHz max"
        subtitle = f"{s.cpu_model} • {topology} • {frequency}{temp} • {self.t('load')} {s.load[0]:.2f}"
        self.draw_detail_header(y, x, width, self.t("processor").upper(), f"{s.cpu:.0f}%", subtitle)
        graph_h = max(5, min(11, height // 3))
        self.draw_chart(y + 4, x, graph_h, width, list(self.sampler.histories["cpu"]), ceiling=100.0)
        self.add(y + 4, x + max(0, width - 5), "100%", self.attr(Theme.MUTED))
        self.add(y + 4 + graph_h, x, self.t("last_samples"), self.attr(Theme.MUTED))
        table_y = y + graph_h + 6
        self.draw_process_table(table_y, x, max(0, height - graph_h - 6), width)

    def draw_cores(self, y: int, x: int, height: int, width: int) -> None:
        """Draw a responsive, paginated grid with one tile per logical CPU."""
        self.box(y, x, height, width, self.attr(Theme.BORDER))
        values = self.snapshot.per_cpu
        inner_x = x + 2
        inner_width = max(1, width - 4)
        self.add(y + 1, inner_x, self.t("cpu_cores"), self.attr(Theme.TEXT, curses.A_BOLD), inner_width)

        temp = f" • {self.snapshot.temperature:.0f}°C" if self.snapshot.temperature is not None else ""
        summary = f"{self.t('logical_cpu', count=len(values))} • {self.snapshot.cpu:.0f}%{temp}"
        core_description = f"{self.snapshot.cpu_model} • {self.t('cores_hint')}"
        self.add(y + 2, inner_x, ellipsize(core_description, max(1, inner_width - len(summary) - 3)), self.attr(Theme.MUTED))
        self.add(y + 2, max(inner_x, x + width - len(summary) - 2), summary, self.attr(Theme.ACCENT, curses.A_BOLD))

        if not values:
            return

        grid_y = y + 4
        card_height = 4
        gap = 2
        columns = max(1, min(len(values), (inner_width + gap) // (20 + gap)))
        card_width = max(12, (inner_width - gap * (columns - 1)) // columns)
        rows = max(1, (height - 5) // card_height)
        page_size = max(1, rows * columns)
        page_count = max(1, math.ceil(len(values) / page_size))
        self.core_page = int(clamp(self.core_page, 0, page_count - 1))
        start = self.core_page * page_size

        if page_count > 1:
            page_text = self.t("page", current=self.core_page + 1, total=page_count)
            self.add(y + 1, x + width - len(page_text) - 2, page_text, self.attr(Theme.MUTED))

        for position, core_index in enumerate(range(start, min(len(values), start + page_size))):
            row, column = divmod(position, columns)
            card_y = grid_y + row * card_height
            card_x = inner_x + column * (card_width + gap)
            if card_y + card_height > y + height:
                break
            value = values[core_index]
            color = self.metric_color(value)
            self.box(card_y, card_x, card_height, card_width, self.attr(Theme.BORDER))
            label = f"CPU {core_index + 1}"
            percentage = f"{value:.0f}%"
            self.add(card_y + 1, card_x + 2, label, self.attr(Theme.TEXT, curses.A_BOLD), max(1, card_width - 4))
            self.add(card_y + 1, card_x + card_width - len(percentage) - 2, percentage, self.attr(color, curses.A_BOLD))
            history_width = max(1, card_width - 4)
            history = list(self.sampler.core_histories[core_index]) if core_index < len(self.sampler.core_histories) else [value]
            self.add(card_y + 2, card_x + 2, sparkline(history, history_width, 100.0), self.attr(color), history_width)

    def draw_gpu(self, y: int, x: int, height: int, width: int) -> None:
        s = self.snapshot
        usage = s.gpu_usage
        primary = s.gpus[0]
        kind = self.t(primary.kind + "_gpu")
        value = f"{usage:.0f}%" if usage is not None else "—"
        self.draw_detail_header(y, x, width, self.t("graphics").upper(), value, f"{kind} • {primary.name}")
        graph_h = max(4, min(8, height // 4))
        self.draw_chart(y + 4, x, graph_h, width, list(self.sampler.histories["gpu"]), ceiling=100.0, primary_color=Theme.SECONDARY)
        details_y = y + graph_h + 6
        self.add(details_y - 1, x, self.t("detected_gpus"), self.attr(Theme.MUTED, curses.A_BOLD), width)
        for index, gpu in enumerate(s.gpus):
            row_y = details_y + index * 4
            if row_y >= y + height:
                break
            label = f"{index + 1}. {gpu.name}"
            gpu_value = f"{gpu.usage:.0f}%" if gpu.usage is not None else self.t("usage_unavailable")
            self.add(row_y, x, ellipsize(label, max(1, width - len(gpu_value) - 2)), self.attr(Theme.TEXT, curses.A_BOLD), width)
            self.add(row_y, max(x, x + width - len(gpu_value)), gpu_value, self.attr(Theme.SECONDARY), len(gpu_value))
            metadata = f"{self.t(gpu.kind + '_gpu')} • {self.t('driver')}: {gpu.driver or '—'} • PCI {gpu.pci_address} • {gpu.card}"
            self.add(row_y + 1, x, ellipsize(metadata, width), self.attr(Theme.MUTED), width)
            temperature = f"{gpu.temperature:.0f}°C" if gpu.temperature is not None else "—"
            maximum = f" / {gpu.frequency_max:.0f} MHz" if gpu.frequency_max else " MHz"
            frequency = f"{gpu.frequency:.0f}{maximum}" if gpu.frequency is not None else "—"
            memory = f"{human_bytes(gpu.vram_used)} / {human_bytes(gpu.vram_total)}" if gpu.vram_total else self.t("shared_memory")
            details = f"{self.t('temperature')}: {temperature} • {self.t('frequency')}: {frequency} • {self.t('video_memory')}: {memory}"
            self.add(row_y + 2, x, ellipsize(details, width), self.attr(Theme.TEXT), width)
            source = gpu.usage_source or "—"
            self.add(row_y + 3, x, f"{self.t('measurement')}: {source}", self.attr(Theme.MUTED), width)

    def draw_battery(self, y: int, x: int, height: int, width: int) -> None:
        batteries = self.snapshot.batteries
        if not batteries:
            self.draw_detail_header(y, x, width, self.t("battery").upper(), "—", self.t("battery_not_detected_hint"))
            self.add(y + 5, x, self.t("battery_not_detected"), self.attr(Theme.MUTED, curses.A_BOLD), width)
            return
        battery = batteries[0]
        status_keys = {
            "charging": "charging",
            "discharging": "discharging",
            "full": "full",
            "not charging": "not_charging",
        }
        status = self.t(status_keys.get(battery.status.lower(), "unknown"))
        identity = " • ".join(value for value in (battery.manufacturer, battery.model) if value) or battery.name
        self.draw_detail_header(y, x, width, self.t("battery").upper(), f"{battery.percent:.0f}%", f"{status} • {identity}")
        self.draw_percent_bar(y + 4, x, width, battery.percent)
        graph_h = max(4, min(8, height // 4))
        self.draw_chart(y + 6, x, graph_h, width, list(self.sampler.histories["battery"]), ceiling=100.0, primary_color=Theme.GOOD)
        row = y + graph_h + 8
        health = f"{battery.health:.1f}%" if battery.health is not None else "—"
        energy = "—"
        if battery.energy_now is not None and battery.energy_full is not None:
            design = f" / {battery.energy_design:.1f} Wh proj." if battery.energy_design is not None else ""
            energy = f"{battery.energy_now:.1f} / {battery.energy_full:.1f} Wh{design}"
        facts = [
            (self.t("battery_health"), health),
            (self.t("battery_cycles"), str(battery.cycles) if battery.cycles is not None else "—"),
            (self.t("battery_energy"), energy),
            (self.t("battery_power"), f"{battery.power:.2f} W" if battery.power is not None else "—"),
            (self.t("battery_time"), duration(battery.time_remaining) if battery.time_remaining is not None else "—"),
            (self.t("battery_technology"), battery.technology or "—"),
        ]
        label_column = min(max(len(label) for label, _ in facts) + 2, max(12, width // 2))
        for label, fact in facts:
            if row >= y + height:
                break
            self.add(row, x, f"{label}:", self.attr(Theme.MUTED, curses.A_BOLD), label_column)
            self.add(row, x + label_column, ellipsize(fact, max(1, width - label_column)), self.attr(Theme.TEXT))
            row += 1

    def draw_memory(self, y: int, x: int, height: int, width: int) -> None:
        s = self.snapshot
        hardware = s.memory_hardware or self.t("memory_hardware_unknown")
        subtitle = f"{hardware} • {self.t('used_available_total', used=human_bytes(s.memory.used), available=human_bytes(s.memory.available), total=human_bytes(s.memory.total))}"
        self.draw_detail_header(y, x, width, self.t("memory").upper(), f"{s.memory.percent:.0f}%", subtitle)
        extra_lines = 1 if s.memory_model else 0
        if s.memory_model:
            self.add(y + 3, x, ellipsize(s.memory_model, width), self.attr(Theme.MUTED), width)
        graph_h = max(5, min(10, height // 3))
        graph_y = y + 4 + extra_lines
        self.draw_chart(graph_y, x, graph_h, width, list(self.sampler.histories["memory"]), ceiling=100.0, primary_color=Theme.SECONDARY)
        details_y = graph_y + graph_h + 1
        self.add(details_y, x, f"RAM  {human_bytes(s.memory.used)} / {human_bytes(s.memory.total)}", self.attr(Theme.TEXT))
        self.draw_percent_bar(details_y + 1, x, width, s.memory.percent, Theme.SECONDARY)
        if s.swap.total:
            self.add(details_y + 2, x, f"SWAP {human_bytes(s.swap.used)} / {human_bytes(s.swap.total)}", self.attr(Theme.MUTED))
        table_y = details_y + 4
        self.draw_process_table(table_y, x, max(0, y + height - table_y), width, memory_sort=True)

    def draw_disk(self, y: int, x: int, height: int, width: int) -> None:
        s = self.snapshot
        subtitle = self.t("used_free", used=human_bytes(s.disk.used), total=human_bytes(s.disk.total), free=human_bytes(s.disk.free))
        self.draw_detail_header(y, x, width, self.t("disk").upper(), self.t("occupied", percent=s.disk.percent), subtitle)
        self.draw_percent_bar(y + 4, x, width, s.disk.percent)
        self.add(y + 6, x, f"{self.t('read')}  {human_rate(s.disk_read_rate)}", self.attr(Theme.GOOD))
        self.add(y + 7, x, f"{self.t('write')}   {human_rate(s.disk_write_rate)}", self.attr(Theme.SECONDARY))
        graph_y = y + 9
        graph_h = max(4, min(12, y + height - graph_y - 2))
        max_value = self.draw_chart(
            graph_y,
            x,
            graph_h,
            width,
            list(self.sampler.histories["disk_read"]),
            list(self.sampler.histories["disk_write"]),
            primary_color=Theme.GOOD,
            secondary_color=Theme.SECONDARY,
        )
        self.add(graph_y, x + max(0, width - len(human_rate(max_value))), human_rate(max_value), self.attr(Theme.MUTED))

    def draw_network(self, y: int, x: int, height: int, width: int) -> None:
        s = self.snapshot
        self.draw_detail_header(y, x, width, self.t("network").upper(), f"↓ {human_rate(s.net_down)}", f"{self.t('sending')} ↑ {human_rate(s.net_up)}")
        graph_h = max(7, min(16, height - 8))
        max_value = self.draw_chart(
            y + 4,
            x,
            graph_h,
            width,
            list(self.sampler.histories["net_down"]),
            list(self.sampler.histories["net_up"]),
            primary_color=Theme.ACCENT,
            secondary_color=Theme.SECONDARY,
        )
        self.add(y + 4, x + max(0, width - len(human_rate(max_value))), human_rate(max_value), self.attr(Theme.MUTED))
        self.add(y + graph_h + 5, x, self.t("downloading"), self.attr(Theme.ACCENT, curses.A_BOLD))
        self.add(y + graph_h + 5, x + 16, self.t("uploading"), self.attr(Theme.SECONDARY, curses.A_BOLD))

    def draw_processes(self, y: int, x: int, height: int, width: int) -> None:
        s = self.snapshot
        subtitle = f"{self.t('threads', count=s.thread_count)} • {self.t('sorting')}: {self.sort_mode.upper()}"
        if self.process_mode:
            subtitle = self.t("process_mode_hint")
        if self.search_query or self.search_active:
            cursor = "▌" if self.search_active else ""
            subtitle = f"{self.t('search')}: {self.search_query}{cursor}"
        if self.status_message and time.monotonic() < self.status_until:
            subtitle = self.status_message
        self.draw_detail_header(y, x, width, self.t("processes").upper(), str(s.process_count), subtitle)
        table_y = y + 4
        self.draw_process_table(
            table_y,
            x,
            max(0, height - 4),
            width,
            interactive=True,
            sort_mode=self.sort_mode,
        )

    def draw_main(self, y: int, x: int, height: int, width: int) -> None:
        component = self.components[self.selected]
        self.box(y, x, height, width, self.attr(Theme.BORDER))
        inner_y, inner_x = y + 2, x + 2
        inner_h, inner_w = height - 4, width - 4
        if inner_h <= 0 or inner_w <= 0:
            return
        handlers = {
            "cpu": self.draw_cpu,
            "gpu": self.draw_gpu,
            "memory": self.draw_memory,
            "disk": self.draw_disk,
            "network": self.draw_network,
            "battery": self.draw_battery,
            "processes": self.draw_processes,
        }
        handlers[component](inner_y, inner_x, inner_h, inner_w)

    def draw_small(self, height: int, width: int) -> None:
        self.add(1, 2, self.t("small_title"), self.attr(Theme.WARN, curses.A_BOLD))
        self.add(3, 2, f"{self.t('terminal')}: {width}×{height}", self.attr(Theme.TEXT))
        self.add(4, 2, self.t("minimum"), self.attr(Theme.MUTED))
        self.add(6, 2, self.t("resize"), self.attr(Theme.MUTED))
        self.add(height - 2, 2, self.t("exit"), self.attr(Theme.MUTED))

    def selected_process(self) -> ProcessRow | None:
        rows = self.sorted_processes()
        if not rows:
            return None
        self.process_index = int(clamp(self.process_index, 0, len(rows) - 1))
        return rows[self.process_index]

    def draw_confirmation(self, height: int, width: int) -> None:
        proc = self.confirm_process
        if proc is None:
            return
        question = self.t("kill_question", name=proc.name, pid=proc.pid)
        warning = self.t("kill_warning")
        modal_width = min(width - 4, max(48, len(question) + 6, len(warning) + 6))
        modal_height = 9
        y = max(1, (height - modal_height) // 2)
        x = max(1, (width - modal_width) // 2)
        self.fill(y, x, modal_height, modal_width, self.attr(Theme.TEXT))
        self.box(y, x, modal_height, modal_width, self.attr(Theme.ACCENT))
        self.add(y + 1, x + 3, self.t("kill_title"), self.attr(Theme.WARN, curses.A_BOLD), modal_width - 6)
        self.add(y + 3, x + 3, ellipsize(question, modal_width - 6), self.attr(Theme.TEXT), modal_width - 6)
        self.add(y + 4, x + 3, ellipsize(warning, modal_width - 6), self.attr(Theme.MUTED), modal_width - 6)

        labels = (self.t("cancel"), self.t("terminate"))
        button_width = max(12, max(len(label) for label in labels) + 4)
        total_width = button_width * 2 + 3
        button_x = x + max(2, (modal_width - total_width) // 2)
        for index, label in enumerate(labels):
            attr = self.attr(Theme.SELECTED, curses.A_BOLD) if index == self.confirm_choice else self.attr(Theme.BORDER, curses.A_BOLD)
            self.add(y + 6, button_x + index * (button_width + 3), f"{label:^{button_width}}", attr, button_width)

    def finish_process(self) -> None:
        proc = self.confirm_process
        self.confirm_process = None
        if proc is None:
            return
        if proc.pid in (0, 1, os.getpid()):
            self.status_message = self.t("kill_protected")
        else:
            try:
                psutil.Process(proc.pid).terminate()
                self.status_message = self.t("kill_sent", name=proc.name, pid=proc.pid)
                self.sampler.last_process_sample = 0.0
            except psutil.NoSuchProcess:
                self.status_message = self.t("kill_gone", pid=proc.pid)
            except psutil.AccessDenied:
                self.status_message = self.t("kill_denied", pid=proc.pid)
            except OSError:
                self.status_message = self.t("kill_denied", pid=proc.pid)
        self.status_until = time.monotonic() + 4.0

    def draw(self) -> None:
        self.screen.erase()
        height, width = self.screen.getmaxyx()
        if height < 20 or width < 72:
            self.draw_small(height, width)
            self.screen.refresh()
            return
        self.draw_header(width)
        self.draw_footer(height, width)
        body_y = 3
        body_h = height - 6
        if self.cores_mode:
            self.draw_cores(body_y, 1, body_h, width - 2)
        else:
            sidebar_w = int(clamp(width * 0.27, 25, 34))
            self.draw_sidebar(body_y, 1, body_h, sidebar_w)
            main_x = sidebar_w + 3
            self.draw_main(body_y, main_x, body_h, width - main_x - 1)
        if self.confirm_process is not None:
            self.draw_confirmation(height, width)
        self.screen.refresh()

    def handle_mouse(self) -> None:
        try:
            _, mx, my, _, state = curses.getmouse()
        except curses.error:
            return
        if not state & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED):
            return
        if self.components[self.selected] == "processes":
            for mode, (y, x, height, width) in self.process_header_regions.items():
                if y <= my < y + height and x <= mx < x + width:
                    self.sort_mode = mode
                    self.process_index = 0
                    self.process_offset = 0
                    return
            for y, x, height, width, row_index in self.process_row_regions:
                if y <= my < y + height and x <= mx < x + width:
                    self.process_mode = True
                    self.process_index = row_index
                    return
        for y, x, height, width, index in self.tile_regions:
            if y <= my < y + height and x <= mx < x + width:
                self.selected = index
                self.process_mode = False
                return

    def cycle_process_sort(self) -> None:
        modes = ("name", *self.process_columns)
        if self.sort_mode not in modes:
            self.sort_mode = modes[0]
        else:
            self.sort_mode = modes[(modes.index(self.sort_mode) + 1) % len(modes)]
        self.process_index = 0
        self.process_offset = 0

    def handle_key(self, key: int) -> None:
        count = len(self.components)
        enter_keys = (10, 13, curses.KEY_ENTER)
        backspace_keys = (curses.KEY_BACKSPACE, 127, 8)

        if self.confirm_process is not None:
            if key in (curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_UP, curses.KEY_DOWN, 9):
                self.confirm_choice = 1 - self.confirm_choice
            elif key in enter_keys:
                if self.confirm_choice == 1:
                    self.finish_process()
                else:
                    self.confirm_process = None
            elif key in (ord("y"), ord("Y"), ord("t"), ord("T")):
                self.finish_process()
            elif key in (27, ord("n"), ord("N")) + backspace_keys:
                self.confirm_process = None
            return

        if self.search_active:
            if key in enter_keys:
                self.search_active = False
                self.process_index = 0
                self.process_offset = 0
            elif key == 27:
                self.search_query = ""
                self.search_active = False
                self.process_index = 0
                self.process_offset = 0
            elif key in backspace_keys:
                self.search_query = self.search_query[:-1]
                self.process_index = 0
                self.process_offset = 0
            elif 32 <= key <= 126:
                self.search_query += chr(key)
                self.process_index = 0
                self.process_offset = 0
            return

        if key in (ord("v"), ord("V")) and self.components[self.selected] == "processes":
            self.process_columns = choose_process_columns(
                self.screen, self.color, self.language, self.process_columns, self.theme,
            )
            if self.sort_mode != "name" and self.sort_mode not in self.process_columns:
                self.sort_mode = "name"
            self._configure_terminal()
            return

        if key in (ord("c"), ord("C")):
            self.theme = choose_theme(self.screen, self.color, self.language, self.theme)
            self._configure_terminal()
            return

        if key in (ord("r"), ord("R")):
            self.cores_mode = not self.cores_mode
            self.core_page = 0
            self.process_mode = False
            return

        if self.cores_mode:
            if key in (ord("q"), ord("Q")):
                self.running = False
            elif key == 27:
                self.cores_mode = False
            elif key in (curses.KEY_LEFT, curses.KEY_UP, curses.KEY_PPAGE):
                self.core_page = max(0, self.core_page - 1)
            elif key in (curses.KEY_RIGHT, curses.KEY_DOWN, curses.KEY_NPAGE):
                self.core_page += 1
            elif key in (ord("l"), ord("L")):
                self.language = choose_language(self.screen, self.color, self.language, self.theme)
                self._configure_terminal()
            return

        if self.process_mode:
            rows = self.sorted_processes()
            if key in (ord("q"), ord("Q")):
                self.running = False
            elif key == 27:
                self.process_mode = False
            elif key in (curses.KEY_UP, ord("k"), ord("K")) and rows:
                self.process_index = (self.process_index - 1) % len(rows)
            elif key in (curses.KEY_DOWN, ord("j"), ord("J")) and rows:
                self.process_index = (self.process_index + 1) % len(rows)
            elif key in (curses.KEY_HOME, ord("g")):
                self.process_index = 0
            elif key in (curses.KEY_END, ord("G")) and rows:
                self.process_index = len(rows) - 1
            elif key in (ord("s"), ord("S")):
                self.cycle_process_sort()
            elif key == ord("/"):
                self.search_active = True
            elif key in backspace_keys:
                proc = self.selected_process()
                if proc is not None:
                    self.confirm_process = proc
                    self.confirm_choice = 0
            return

        if key in (ord("q"), ord("Q"), 27):
            self.running = False
        elif key in (curses.KEY_UP, ord("k"), ord("K")):
            self.selected = (self.selected - 1) % count
        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            self.selected = (self.selected + 1) % count
        elif key in (curses.KEY_HOME, ord("g")):
            self.selected = 0
        elif key in (curses.KEY_END, ord("G")):
            self.selected = count - 1
        elif key in enter_keys and self.components[self.selected] == "processes":
            self.process_mode = True
            self.process_index = 0
            self.process_offset = 0
        elif key in (ord("s"), ord("S")):
            self.cycle_process_sort()
        elif key == ord("/") and self.components[self.selected] == "processes":
            self.process_mode = True
            self.search_active = True
            self.process_index = 0
            self.process_offset = 0
        elif key in (ord("l"), ord("L")):
            self.language = choose_language(self.screen, self.color, self.language, self.theme)
            self._configure_terminal()
        elif key in (ord("+"), ord("=")):
            self.interval = max(0.25, self.interval - 0.25)
        elif key in (ord("-"), ord("_")):
            self.interval = min(5.0, self.interval + 0.25)
        elif key == curses.KEY_MOUSE:
            self.handle_mouse()

    def run(self) -> None:
        dirty = True
        while self.running:
            now = time.monotonic()
            if now - self.last_sample >= self.interval:
                self.snapshot = self.sampler.sample()
                self.last_sample = now
                dirty = True
            if dirty:
                self.draw()
                dirty = False

            # Wait until either input arrives or the next sample is due.  The
            # first version redrew at 10 FPS even when nothing had changed;
            # event-driven drawing keeps miltop's own CPU use close to zero.
            remaining = max(0.02, self.interval - (time.monotonic() - self.last_sample))
            self.screen.timeout(max(20, min(250, int(remaining * 1000))))
            key = self.screen.getch()
            if key != -1:
                self.handle_key(key)
                dirty = True


def print_snapshot(language: str = "pl") -> None:
    sampler = Sampler(background_hardware=False)
    sampler._load_gpu_names()
    time.sleep(1.0)
    snap = sampler.sample()
    print(f"CPU       {snap.cpu:5.1f}%")
    for gpu in snap.gpus:
        usage = f"{gpu.usage:5.1f}%" if gpu.usage is not None else "   n/a"
        temperature = f" • {gpu.temperature:.0f}°C" if gpu.temperature is not None else ""
        frequency = f" • {gpu.frequency:.0f} MHz" if gpu.frequency is not None else ""
        print(f"GPU       {usage}  {text(language, gpu.kind + '_gpu')} • {gpu.name}{temperature}{frequency}")
    if snap.batteries:
        battery = snap.batteries[0]
        health = f" • {text(language, 'battery_health')} {battery.health:.1f}%" if battery.health is not None else ""
        print(f"{text(language, 'battery'):<10}{battery.percent:5.1f}%  {battery.manufacturer} {battery.model}{health}")
    else:
        print(f"{text(language, 'battery'):<10}{text(language, 'battery_not_detected')}")
    print(f"{text(language, 'memory'):<10}{snap.memory.percent:5.1f}%  {human_bytes(snap.memory.used)} / {human_bytes(snap.memory.total)}")
    print(f"{text(language, 'disk'):<10}{snap.disk.percent:5.1f}%  R {human_rate(snap.disk_read_rate)}  W {human_rate(snap.disk_write_rate)}")
    print(f"{text(language, 'network'):<19}↓ {human_rate(snap.net_down)}  ↑ {human_rate(snap.net_up)}")
    print(f"{text(language, 'processes'):<10}{snap.process_count:5d}   ({text(language, 'threads', count=snap.thread_count)})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lekki, kafelkowy menedżer zasobów dla terminala.")
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="czas odświeżania w sekundach (domyślnie: 1)")
    parser.add_argument("--no-color", action="store_true", help="wyłącz kolory")
    parser.add_argument("--snapshot", action="store_true", help="wypisz pojedynczy pomiar bez interfejsu")
    parser.add_argument("--version", action="version", version=f"miltop {VERSION}")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.snapshot:
        print_snapshot(load_language() or "pl")
        return 0
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("miltop: interfejs wymaga terminala (użyj --snapshot dla pojedynczego pomiaru)", file=sys.stderr)
        return 2
    os.environ.setdefault("ESCDELAY", "25")
    signal.signal(signal.SIGINT, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        def run_session(screen: Any) -> None:
            language = load_language()
            theme = load_theme()
            if language is None:
                language = choose_language(screen, not args.no_color, theme=theme)
            MiltopApp(screen, args.interval, not args.no_color, language, theme).run()

        curses.wrapper(run_session)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
