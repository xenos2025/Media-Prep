# Contributing

Thanks for helping improve Media Prep.

## Layout

| Path | Role |
| --- | --- |
| `skill/media-prep-workbench/` | Canonical Agent Skill + `scripts/media_prep.py` |
| `src/media_prep/` | Installable `python -m media_prep` / `media-prep` entry |
| `docs/` | Human docs and upgrade notes |
| `tests/` | Smoke / regression tests |
| `install.ps1` / `install.sh` | Copy the skill into Cursor skills dirs |

## Rules

1. Prefer editing the skill package under `skill/media-prep-workbench/` for
   agent workflow and CLI behavior; keep `src/media_prep/` as a thin entry.
2. Keep the core **project-neutral**: no client names, SKUs, SEO taxonomies,
   or live store credentials in the skill or examples.
3. Preserve originals by default. Do not add delete/overwrite-of-source paths
   without an explicit, reviewed flag and docs update.
4. Enhancement presets that shift color (`auto` / RGB presets) stay opt-in;
   color-critical defaults remain `none` / `texture-safe`.
5. Shopify-specific limits belong in profile docs / `--profile shopify`, not
   as the only product story.
6. Update `CHANGELOG.md` under `[Unreleased]` for user-visible changes.
7. Never commit secrets, client PII, store tokens, or real media batches.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[mozjpeg]"
# FFmpeg (ffmpeg + ffprobe) must be on PATH for video commands
python -m media_prep -h
python -m unittest discover tests -v
```

## Pull requests

1. Branch from `main`.
2. Keep the PR focused (one concern when possible).
3. Describe **why** the change is needed; link issues if any.
4. Confirm smoke tests / relevant CLI checks are green.
5. Follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Report vulnerabilities privately per [SECURITY.md](SECURITY.md). Do not open
public issues for security findings.
