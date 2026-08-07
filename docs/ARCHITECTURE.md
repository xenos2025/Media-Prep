# Architecture

Media Prep is a **local workbench**: Agent Skill instructions plus a Python CLI.
It does not upload to Shopify or call store APIs.

```text
User / Agent
    │
    ├─ SKILL.md workflow (inspect → name map → process → QA)
    │
    └─ media_prep.py  (or python -m media_prep)
           ├─ Pillow  → images
           └─ FFmpeg  → videos
                  │
                  └─ isolated out/  (maps, contact sheets, processed media)
```

## Packages

| Piece | Responsibility |
| --- | --- |
| `skill/media-prep-workbench/SKILL.md` | Agent contract: safety, naming, command recipes |
| `skill/.../scripts/media_prep.py` | All inspect / process / trim logic |
| `skill/.../references/` | Default presets; Shopify as a profile note |
| `src/media_prep/` | Thin launcher so `pip install -e .` works |
| `install.ps1` / `install.sh` | Copy skill into Cursor skills dirs |
| `plugin.json` | Machine-readable skill pack metadata |

## Profiles

`--profile shopify` (default) keeps storefront-oriented defaults and
platform QA warnings. `--profile generic` uses the same encode path with
softer platform-specific copy. See [generality-upgrade.md](generality-upgrade.md).

## Safety invariants

- Source files are read-only by default
- Outputs go to a new run folder under `media-prep-workbench\`
- Exact duplicates skipped via SHA-256
- Generated media strips metadata unless preservation is requested
- Product video audio removed by default
