# AGENTS.md — photo-autocopy

## What this is

A Windows Python tool that organizes photos by EXIF capture date into `YYYYMMDD/` subdirectories. Two entry points:

- `photo_autocopy.py` — CLI, reads `config.ini`
- `photo_autocopy_gui.py` — tkinter GUI, also reads/writes `config.ini`

`photo_autocopy.exe` is a pre-built PyInstaller binary (spec: `PhotoAutocopy.spec`). Do not edit the `.spec` unless asked.

## Commands

```bash
pip install -r requirements.txt   # exifread, tqdm (tkinter is stdlib)
python photo_autocopy.py          # CLI mode
python photo_autocopy_gui.py      # GUI mode
```

No test suite, no linter, no type checker configured.

## Config (`config.ini`)

INI format with two sections: `[Paths]` and `[Settings]`. Key fields:

- `source_path` — folder to scan
- `output_path` — destination root (date subdirs created here)
- `start_date` — only photos on/after this date are copied

**Date format quirk**: Code prefers `YYYYMMDD` internally but accepts `YYYY-MM-DD` with a runtime warning. If modifying date parsing, update both `photo_autocopy.py` and `photo_autocopy_gui.py` — they have duplicated logic.

## Architecture notes

- Both scripts duplicate the core logic (EXIF extraction, file walking, conflict resolution). Changes to one must be mirrored in the other.
- EXIF date lookup order: `EXIF DateTimeOriginal` → `Image DateTime` → file mtime fallback.
- File conflicts: appends `_1`, `_2`, etc. before extension.
- Supported extensions: `.jpg .jpeg .png .gif .bmp .tiff .raw .nef` (case-insensitive).
- GUI runs processing in a daemon thread; UI updates via `root.after()`.

## Platform

Windows-only. Paths use backslashes and may contain Chinese characters (e.g., `D:\hxzhang\照片\phone-sync`). GUI font is `Microsoft YaHei UI`.

## If modifying

- Keep both entry points in sync — they share no code.
- `config.ini` encoding is `utf-8`; use `encoding='utf-8'` in all `config.read()` / `open()` calls.
- The CLI has an interactive prompt (`input()`) when config is missing — GUI does not.
- PyInstaller build: `pyinstaller PhotoAutocopy.spec` (bundles `photo_autocopy.py` only, not the GUI).
