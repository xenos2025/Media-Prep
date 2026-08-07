# Troubleshooting

## `media-prep` is not recognized

The console script may not be on `PATH`. Prefer:

```powershell
python -m media_prep -h
```

Or call the skill script directly:

```powershell
python skill\media-prep-workbench\scripts\media_prep.py -h
```

## Pillow missing

```powershell
pip install -e .
# or
pip install -r requirements.txt
```

## FFmpeg / ffprobe not found

Install FFmpeg and ensure both `ffmpeg` and `ffprobe` are on `PATH`, then
re-open the terminal.

## Windows path mojibake (Chinese folder names)

```powershell
$env:PYTHONIOENCODING = 'utf-8'
```

Or use PowerShell 7+. The CLI also attempts to set the console code page to UTF-8.

## Installer refuses destination

Install targets must end with the skill leaf name `media-prep-workbench`, and
cannot be `$HOME`, the repo root, or a drive root. Pass `-Force` / `--force`
only after reviewing the existing destination.

## Color looks wrong after enhance

`--enhance` defaults to `none`. RGB presets can shift pastels and fabrics.
Use `none` or `texture-safe`, and review a single proof image before batching.

## Cover crop cuts the product

Review `image-process-contact-sheet.jpg`. Use `--focus-x` / `--focus-y`, a
`--focus-map` CSV, or switch to `--fit pad`.
