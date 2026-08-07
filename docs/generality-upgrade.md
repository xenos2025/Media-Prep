# Generality Upgrade

Turn the personal Codex skill into a reusable, project-owned media workbench. Shopify remains a first-class **target profile**, not the only product story.

## Goals

1. **Repo is source of truth** — skill package, CLI, and presets live here; personal skill dirs sync from the project.
2. **Project-neutral core** — no client names, SKUs, or SEO taxonomies in the skill or script.
3. **Profiles over hard-coding** — processing knobs and QA warnings differ by target (`shopify`, later `generic` / site-specific).
4. **Installable CLI** — `pip install -e .` exposes `media-prep` without remembering the skill script path.
5. **Safe defaults** — originals read-only; outputs under isolated `media-prep-workbench\` run folders.

## Current status (v0.1)

| Item | Status |
|------|--------|
| Skill copied into `skill/media-prep-workbench/` | done |
| Cursor junction `.cursor/skills/...` | done |
| Packaging (`pyproject.toml`, `media-prep` entry) | done |
| `--profile` on process commands | done (`shopify` / `generic`) |
| Split Shopify limits out of core helpers | planned |
| Automated tests + sample fixtures | planned |
| Cursor installers (`install.ps1` / `install.sh`) | done |
| OSS packaging (LICENSE, community docs, CI) | done |
| Codex personal-skill sync notes | documented in INSTALLATION |

## Profile model

| Profile | Intent |
|---------|--------|
| `shopify` (default) | 2048px images, Rec.709 SDR video masters, Shopify limit warnings, storefront-oriented audio-off default |
| `generic` | Same codecs/pipeline, softer platform warnings; long-edge and CRF still overridable via flags |

Future: project-local profile YAML (max edge, target KB, aspect presets) without editing the skill.

## Next slices (suggested order)

1. Move verified Shopify limits into `references/profiles/shopify.md`; keep shared storefront guidance in presets.
2. Expand fixtures + inspect/process smoke tests (synthetic media only).
3. Optional: per-orientation aspect maps (`landscape→1:1`, `portrait→3:4`) as a named recipe, not a one-off flag soup.
4. ~~Publish the GitHub remote~~ → https://github.com/xenos2025/Media-Prep

## Non-goals (for now)

- Shopify Admin upload / theme edits
- AI background removal or creative retouch
- Hosting a web UI
