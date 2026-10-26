# Changelog

All notable changes to this project will be documented in this file.

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
