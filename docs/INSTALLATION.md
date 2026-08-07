# Installation

## Requirements

- Python 3.10+
- [Pillow](https://pillow.readthedocs.io/) (`pip` installs it with the package)
- [FFmpeg](https://ffmpeg.org/) on `PATH` (`ffmpeg` + `ffprobe`) for video commands
- Optional: `mozjpeg-lossless-optimization` via `pip install -e ".[mozjpeg]"`

## Option A — editable package (recommended for contributors)

```powershell
git clone https://github.com/xenos2025/Media-Prep.git
cd media-prep
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python -m media_prep -h
```

## Option B — Cursor Agent Skill only

Copy the skill into your Cursor skills directory:

```powershell
# user-global
.\install.ps1

# or into another project
.\install.ps1 -Project D:\path\to\other-project

# overwrite an existing install
.\install.ps1 -Force
```

Bash:

```bash
chmod +x install.sh
./install.sh
./install.sh --project /path/to/other-project
./install.sh --force
```

Then ask the agent to use `/media-prep-workbench` (or load
`skill/media-prep-workbench/SKILL.md` from this repo).

## Option C — run the script without packaging

```powershell
python skill\media-prep-workbench\scripts\media_prep.py inspect-images --src "E:\images" --out "E:\images\media-prep-workbench\task-ts\inspect-images"
```

## Codex / personal skill sync

This repo is the source of truth. To refresh a personal Codex skill dir, either:

- re-run a junction/copy from `skill/media-prep-workbench/` into `~/.codex/skills/media-prep-workbench`, or
- use `install.ps1` / `install.sh` for Cursor and keep Codex in sync the same way.
