# AGENTS.md — photo-autocopy

## What this is

A Windows Python tool that organizes photos by EXIF capture date into `YYYYMMDD/` subdirectories. Two entry points:

- `photo_autocopy.py` — CLI with `argparse`, reads `config.ini`
- `photo_autocopy_gui.py` — tkinter GUI, reads/writes `config.ini`

`photo_autocopy.exe` is a pre-built PyInstaller binary (spec: `PhotoAutocopy.spec`). Do not edit the `.spec` unless asked.

## Commands

```bash
pip install -r requirements.txt   # exifread only (tkinter is stdlib)
python photo_autocopy.py          # CLI mode
python photo_autocopy.py --dry-run  # preview mode (no copy)
python photo_autocopy_gui.py      # GUI mode
```

No test suite, no linter, no type checker configured.

## Architecture

Core logic is in `core/` package:

- `core/config.py` — `AppConfig` dataclass, INI load/save, validation
- `core/exif.py` — EXIF date extraction with `stop_tag` optimization
- `core/organizer.py` — `PhotoOrganizer` class with dry-run and logging

Both CLI and GUI import from `core/` — no duplicated logic.

## Config (`config.ini`)

INI format with two sections: `[Paths]` and `[Settings]`. Key fields:

- `source_path` — folder to scan
- `output_path` — destination root (date subdirs created here)
- `start_date` — only photos on/after this date are copied (YYYYMMDD preferred, YYYY-MM-DD accepted)

## Features

- **Dry-run mode**: `--dry-run` flag or GUI checkbox, preview without copying
- **Operation logging**: `--log-file` flag writes detailed log with timestamps
- **HEIC/HEIF support**: Apple photo formats included in supported extensions
- **EXIF optimization**: Uses `stop_tag` and `details=False` for faster reading
- **Thread-safe GUI**: All UI updates via `root.after()`, stop button support

## Supported formats

`.jpg .jpeg .png .gif .bmp .tiff .raw .nef .arw .cr2 .cr3 .dng .heic .heif`

## Platform

Windows-only. Paths use backslashes and may contain Chinese characters. GUI font is `Microsoft YaHei UI`.

## If modifying

- Core logic goes in `core/`, not in the entry point scripts
- `config.ini` encoding is `utf-8`; use `encoding='utf-8'` in all file I/O
- EXIF date tags priority: `EXIF DateTimeOriginal` → `EXIF DateTimeDigitized` → `Image DateTime`
- PyInstaller build: `pyinstaller PhotoAutocopy.spec` (bundles CLI only)
