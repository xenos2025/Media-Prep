# AGENTS.md

Guidance for coding agents working **on this repository**.

> Scope: this file configures agents editing the media-prep workbench itself.
> End users install the skill from `skill/media-prep-workbench/`; they do not
> need to copy this file.

## Layout

| Path | Role |
| --- | --- |
| `skill/media-prep-workbench/` | Canonical Agent Skill + CLI script |
| `skill/media-prep-workbench/scripts/media_prep.py` | Inspect / process / trim implementation |
| `skill/media-prep-workbench/references/` | Storefront presets and profile notes |
| `src/media_prep/` | Thin installable entry (`python -m media_prep`) |
| `docs/` | Human docs including generality upgrade |
| `tests/` | Smoke / regression suite |
| `install.ps1` / `install.sh` | Copy skill into Cursor skills dirs |

## Rules

1. Prefer editing the skill package under `skill/media-prep-workbench/` for
   product behavior; keep `src/media_prep/` as a thin launcher.
2. Keep the workbench **project-neutral** — client taxonomy and SEO decisions
   stay in the consuming project, not in this skill.
3. Default to local-only file work. Do not add Shopify upload, theme edits,
   delete-originals, or overwrite-source flows unless the user explicitly
   scopes that work and docs/safety rules are updated.
4. Write outputs under isolated `media-prep-workbench\<task>-<timestamp>\`
   folders by default; exclude those run folders from future source scans.
5. Enhancement that shifts color is opt-in (`--enhance none` default). Prefer
   `texture-safe` for fabric/textile colorways when clarity is needed.
6. After CLI behavior changes, run `python -m unittest discover tests -v` and
   a quick `python -m media_prep <cmd> -h` check.
7. Never commit secrets, client PII, or real media/report dumps.

## Quick commands

```bash
python -m pip install -e .
python -m media_prep -h
python -m media_prep process-images -h
python -m unittest discover tests -v
python skill/media-prep-workbench/scripts/media_prep.py inspect-images --src path/to/images --out path/to/out/inspect-images
```
