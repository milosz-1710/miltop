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


VERSION = "1.2.0"
BLOCKS = " ▁▂▃▄▅▆▇█"
CONFIG_FILE = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "miltop" / "config.json"
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
        "memory": "Pamięć",
        "used_of": "{used} z {total}",
        "disk": "Dysk",
        "network": "Sieć",
        "processes": "Procesy",
        "footer": "↑↓ wybór   Enter otwórz   R rdzenie   L język   Q wyjście",
        "footer_process": "↑↓ proces   S CPU/RAM   Backspace zakończ   Esc wróć   Q wyjście",
        "footer_confirm": "←→ wybór   Enter zatwierdź   Esc anuluj",
        "footer_cores": "R/Esc wróć   PgUp/PgDn strona   L język   Q wyjście",
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
        "memory": "Memory",
        "used_of": "{used} of {total}",
        "disk": "Disk",
        "network": "Network",
        "processes": "Processes",
        "footer": "↑↓ select   Enter open   R cores   L language   Q quit",
        "footer_process": "↑↓ process   S CPU/RAM   Backspace end   Esc back   Q quit",
        "footer_confirm": "←→ select   Enter confirm   Esc cancel",
        "footer_cores": "R/Esc back   PgUp/PgDn page   L language   Q quit",
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
    },
}


def text(language: str, key: str, **values: Any) -> str:
    template = TEXTS.get(language, TEXTS["pl"]).get(key, key)
    return template.format(**values)


def load_language() -> str | None:
    try:
        language = json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get("language")
        return language if language in TEXTS else None
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def save_language(language: str) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = CONFIG_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps({"language": language}, indent=2) + "\n", encoding="utf-8")
    temporary.replace(CONFIG_FILE)


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


class Sampler:
    def __init__(self, history_size: int = 600) -> None:
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
        threading.Thread(target=self._load_memory_hardware, name="miltop-hardware", daemon=True).start()
        self.gpu_path, self.gpu_name = self._find_gpu()
        psutil.cpu_percent(interval=None, percpu=True)

    def _load_memory_hardware(self) -> None:
        self.memory_hardware, self.memory_model = self._read_memory_hardware()

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
    def _find_gpu() -> tuple[Path | None, str]:
        for card in sorted(Path("/sys/class/drm").glob("card[0-9]*")):
            busy = card / "device" / "gpu_busy_percent"
            if not busy.exists():
                continue
            name = card.name.upper()
            vendor_file = card / "device" / "vendor"
            try:
                vendor = vendor_file.read_text().strip().lower()
                name = {"0x1002": "AMD GPU", "0x8086": "Intel GPU", "0x10de": "NVIDIA GPU"}.get(vendor, name)
            except OSError:
                pass
            return busy, name
        return None, ""

    def _read_gpu(self) -> float | None:
        if self.gpu_path is None:
            return None
        try:
            return clamp(float(self.gpu_path.read_text().strip()), 0.0, 100.0)
        except (OSError, ValueError):
            return None

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

        # Enumerating every /proc entry is the most expensive part of a task
        # manager.  Hardware graphs stay live every tick, while the process
        # table refreshes every two seconds - visually immediate, much lighter.
        process_dt = now - self.last_process_sample if self.last_process_sample else dt
        if not self.cached_processes or process_dt >= 2.0:
            self.cached_processes, self.cached_process_count, self.cached_thread_count = self._processes(process_dt)
            self.last_process_sample = now
        processes = self.cached_processes
        process_count = self.cached_process_count
        thread_count = self.cached_thread_count
        freq = psutil.cpu_freq()
        gpu = self._read_gpu()

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
            gpu_name=self.gpu_name,
            gpu_usage=gpu,
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

    @staticmethod
    def init(enabled: bool) -> None:
        if not enabled or not curses.has_colors():
            return
        curses.start_color()
        curses.use_default_colors()
        if curses.COLORS >= 256:
            definitions = {
                Theme.TEXT: (252, -1),
                Theme.MUTED: (244, -1),
                Theme.ACCENT: (81, -1),
                Theme.SELECTED: (255, 24),
                Theme.GOOD: (114, -1),
                Theme.WARN: (221, -1),
                Theme.BAD: (203, -1),
                Theme.BORDER: (240, -1),
                Theme.SECONDARY: (177, -1),
            }
        else:
            definitions = {
                Theme.TEXT: (curses.COLOR_WHITE, -1),
                Theme.MUTED: (curses.COLOR_WHITE, -1),
                Theme.ACCENT: (curses.COLOR_CYAN, -1),
                Theme.SELECTED: (curses.COLOR_BLACK, curses.COLOR_CYAN),
                Theme.GOOD: (curses.COLOR_GREEN, -1),
                Theme.WARN: (curses.COLOR_YELLOW, -1),
                Theme.BAD: (curses.COLOR_RED, -1),
                Theme.BORDER: (curses.COLOR_WHITE, -1),
                Theme.SECONDARY: (curses.COLOR_MAGENTA, -1),
            }
        for pair, (fg, bg) in definitions.items():
            try:
                curses.init_pair(pair, fg, bg)
            except curses.error:
                pass


def choose_language(screen: Any, color: bool, current: str = "pl") -> str:
    """Show the first-run language screen and persist the selection."""
    options = [("pl", "Polski"), ("en", "English")]
    selected = next((index for index, item in enumerate(options) if item[0] == current), 0)
    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()
    screen.keypad(True)
    screen.timeout(-1)
    Theme.init(color)

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


class MiltopApp:
    def __init__(self, screen: Any, interval: float, color: bool = True, language: str = "pl") -> None:
        self.screen = screen
        self.interval = clamp(interval, 0.25, 5.0)
        self.sampler = Sampler()
        self.snapshot = self.sampler.sample()
        self.selected = 0
        self.running = True
        self.color = color
        self.language = language if language in TEXTS else "pl"
        self.last_sample = time.monotonic()
        self.sort_mode = "cpu"
        self.process_mode = False
        self.cores_mode = False
        self.core_page = 0
        self.process_index = 0
        self.process_offset = 0
        self.confirm_process: ProcessRow | None = None
        self.confirm_choice = 0
        self.status_message = ""
        self.status_until = 0.0
        self.tile_regions: list[tuple[int, int, int, int]] = []
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
        Theme.init(self.color)
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        except curses.error:
            pass

    @property
    def components(self) -> list[str]:
        items = ["cpu", "memory", "disk", "network", "processes"]
        if self.snapshot.gpu_usage is not None:
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
            return s.gpu_name or "GPU", f"{s.gpu_usage or 0:.0f}%", self.t("gpu_usage"), list(h["gpu"]), 100.0
        if component == "memory":
            hardware = s.memory_hardware or self.t("memory_hardware_unknown")
            detail = f"{hardware} • {human_bytes(s.memory.used)} / {human_bytes(s.memory.total)}"
            return self.t("memory"), f"{s.memory.percent:.0f}%", detail, list(h["memory"]), 100.0
        if component == "disk":
            return self.t("disk"), f"{s.disk.percent:.0f}%", f"R {human_rate(s.disk_read_rate)}  W {human_rate(s.disk_write_rate)}", list(h["disk"]), 100.0
        if component == "network":
            return self.t("network"), human_rate(s.net_down), f"↓ {human_rate(s.net_down)}  ↑ {human_rate(s.net_up)}", list(h["net_down"]), None
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
            help_text = self.t("footer_process")
        else:
            help_text = self.t("footer")
        self.add(height - 1, 2, ellipsize(help_text, width - 4), self.attr(Theme.MUTED))

    def draw_sidebar(self, y: int, x: int, height: int, width: int) -> None:
        self.add(y, x + 1, self.t("components"), self.attr(Theme.MUTED, curses.A_BOLD))
        components = self.components
        self.selected = min(self.selected, len(components) - 1)
        available = height - 2
        tile_h = 4 if available >= len(components) * 4 else 3
        self.tile_regions = []
        for index, component in enumerate(components):
            tile_y = y + 2 + index * tile_h
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
            self.tile_regions.append((tile_y, x, tile_h, width))

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

    def sorted_processes(self, memory_sort: bool | None = None) -> list[ProcessRow]:
        if memory_sort is None:
            memory_sort = self.sort_mode == "ram"
        return sorted(
            self.snapshot.processes,
            key=(lambda proc: proc.memory) if memory_sort else (lambda proc: proc.cpu),
            reverse=True,
        )

    def draw_process_table(
        self,
        y: int,
        x: int,
        height: int,
        width: int,
        memory_sort: bool = False,
        interactive: bool = False,
    ) -> None:
        if height < 3:
            return
        rows = self.sorted_processes(memory_sort)
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
        name_width = max(8, width - 25)
        self.add(y, x, "PID", self.attr(Theme.MUTED, curses.A_BOLD), 7)
        self.add(y, x + 8, self.t("process"), self.attr(Theme.MUTED, curses.A_BOLD), name_width)
        self.add(y, x + width - 15, "CPU", self.attr(Theme.MUTED, curses.A_BOLD), 6)
        self.add(y, x + width - 8, "RAM", self.attr(Theme.MUTED, curses.A_BOLD), 8)
        self.line(y + 1, x, width, "─", self.attr(Theme.BORDER))
        for index, proc in enumerate(shown):
            row_y = y + 2 + index
            actual_index = self.process_offset + index if interactive else index
            selected = interactive and actual_index == self.process_index
            row_attr = self.attr(Theme.SELECTED) if selected else 0
            if selected:
                self.fill(row_y, x, 1, width, row_attr)
            self.add(row_y, x, str(proc.pid), row_attr or self.attr(Theme.MUTED), 7)
            self.add(row_y, x + 8, ellipsize(proc.name, name_width - 1), row_attr or self.attr(Theme.TEXT), name_width)
            cpu_text = f"{proc.cpu:4.0f}%"
            self.add(row_y, x + width - 15, cpu_text, row_attr or self.attr(self.metric_color(min(proc.cpu, 100.0))), 6)
            self.add(row_y, x + width - 8, human_bytes(proc.memory).replace(" ", ""), row_attr or self.attr(Theme.TEXT), 8)

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
        usage = s.gpu_usage or 0.0
        self.draw_detail_header(y, x, width, (s.gpu_name or "GPU").upper(), f"{usage:.0f}%", self.t("gpu_usage"))
        graph_h = max(6, min(14, height // 2))
        self.draw_chart(y + 4, x, graph_h, width, list(self.sampler.histories["gpu"]), ceiling=100.0, primary_color=Theme.SECONDARY)
        self.add(y + graph_h + 5, x, self.t("current_usage"), self.attr(Theme.MUTED))
        self.draw_percent_bar(y + graph_h + 6, x, width, usage, Theme.SECONDARY)

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
        if self.status_message and time.monotonic() < self.status_until:
            subtitle = self.status_message
        self.draw_detail_header(y, x, width, self.t("processes").upper(), str(s.process_count), subtitle)
        table_y = y + 4
        self.draw_process_table(
            table_y,
            x,
            max(0, height - 4),
            width,
            memory_sort=self.sort_mode == "ram",
            interactive=self.process_mode,
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
        for index, (y, x, height, width) in enumerate(self.tile_regions):
            if y <= my < y + height and x <= mx < x + width:
                self.selected = index
                self.process_mode = False
                return

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
                self.language = choose_language(self.screen, self.color, self.language)
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
                self.sort_mode = "ram" if self.sort_mode == "cpu" else "cpu"
                self.process_index = 0
                self.process_offset = 0
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
            self.sort_mode = "ram" if self.sort_mode == "cpu" else "cpu"
        elif key in (ord("l"), ord("L")):
            self.language = choose_language(self.screen, self.color, self.language)
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
    sampler = Sampler()
    time.sleep(0.12)
    snap = sampler.sample()
    print(f"CPU       {snap.cpu:5.1f}%")
    if snap.gpu_usage is not None:
        print(f"{(snap.gpu_name or 'GPU'):<9} {snap.gpu_usage:5.1f}%")
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
            if language is None:
                language = choose_language(screen, not args.no_color)
            MiltopApp(screen, args.interval, not args.no_color, language).run()

        curses.wrapper(run_session)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
