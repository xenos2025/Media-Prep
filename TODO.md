# Roadmap / TODO

Open an issue with the `roadmap` label to propose items.

Detailed upgrade notes: [docs/generality-upgrade.md](docs/generality-upgrade.md).

## Near term

- [x] Move skill into this repo (`skill/media-prep-workbench/`)
- [x] Installable `python -m media_prep` entry
- [x] `--profile shopify|generic`
- [x] OSS packaging (LICENSE, community docs, plugin.json, installers, CI)
- [ ] Split Shopify limits into `references/profiles/shopify.md`
- [ ] Fixture folder + smoke tests for inspect/process (synthetic media only)
- [ ] Per-orientation aspect recipe (`landscape→1:1`, `portrait→3:4`)
- [ ] Optional Codex skill sync notes alongside Cursor installers

## Later

- [ ] Project-local profile YAML (max edge, target KB, aspect presets)
- [ ] Uninstall.ps1 / uninstall.sh for Cursor skills dir
- [ ] Marketplace / `npx skills add` notes once the public repo URL is set

## Non-goals (for now)

- Shopify Admin upload / theme edits
- AI background removal or creative retouch
- Hosting a web UI
