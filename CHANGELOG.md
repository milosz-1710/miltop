# Changelog

All notable changes to this project will be documented in this file.

## [1.4.0] - 2026-11-02

### Added

- real Intel GPU utilization from unprivileged DRM `fdinfo` engine counters
  when `gpu_busy_percent` is unavailable;
- NVIDIA utilization, temperature, VRAM and clock details through `nvidia-smi`;
- GPU temperature, current/max clock, graphics memory, driver and measurement
  source details;
- a battery component with model, manufacturer, technology, charge, health,
  cycle count, energy, power draw and estimated remaining time;
- a clear "No battery detected" state for desktop computers;
- live process-name/PID search opened with `/`;
- process GPU activity and an explicitly labelled estimated energy-impact score;
- persistent process-column visibility settings opened with `V` for CPU, RAM,
  GPU and energy impact;
- five process sorting modes: name, CPU, RAM, GPU and energy impact;
- clickable process table headers and rows.

### Changed

- GPU sampling now reads only file descriptors that actually point to DRM
  devices, reducing `/proc` work by roughly four times on busy desktops;
- battery and NVIDIA helper data are cached between fast refresh ticks;
- the component sidebar now follows the selection in short terminals, keeping
  the new Battery and Processes tiles reachable;
- snapshot output now includes live GPU load and battery health.

## [1.3.0] - 2026-11-02

### Added

- detection of every DRM graphics adapter, including vendor and full PCI model;
- best-effort classification of integrated and dedicated GPUs;
- a graphics details view listing multiple adapters and their PCI addresses;
- live GPU usage when the Linux driver exposes `gpu_busy_percent`;
- six persistent interface color themes: cyan, green, red, blue, purple and
  amber, selectable from the new `C` color settings screen.

### Changed

- graphics adapters remain visible even when their driver does not expose a
  utilization counter;
- DRM connector entries such as HDMI and DisplayPort are no longer mistaken
  for additional graphics cards;
- language changes now preserve the selected color theme.

## [1.2.0] - 2026-10-26

### Added

- responsive per-core CPU view opened with `R`;
- live load percentage and short activity graph for every logical CPU;
- automatic pagination for computers with many logical CPUs;
- Polish and English help text for the new view.
- processor model, physical-core/thread topology and current/max frequency;
- best-effort RAM generation, speed, module layout, manufacturer and part
  number detection through unprivileged `inxi` data.

### Changed

- `R` now toggles the processor-core view; monitoring continues to refresh
  automatically in the background.

## [1.1.0] - 2026-10-26

### Added

- tile-based CPU, memory, disk, network and process views;
- interactive process list with CPU/RAM sorting;
- safe SIGTERM confirmation on Backspace;
- first-run Polish/English language selection;
- keyboard and mouse navigation;
- configurable refresh interval and snapshot mode;
- event-driven drawing to keep idle CPU usage low.
