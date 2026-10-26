# Contributing to miltop

Thank you for helping improve miltop.

1. Open an issue before making a large behavioral or interface change.
2. Fork the repository and create a focused branch.
3. Keep the application lightweight and usable with both keyboard and mouse.
4. Update both Polish and English interface text when adding visible strings.
5. Run the checks below before opening a pull request.

```bash
python3 -m py_compile miltop.py
python3 miltop.py --snapshot
```

Process termination must remain opt-in, show a confirmation and use SIGTERM by
default. Pull requests must not add telemetry or require root privileges for
normal monitoring.
