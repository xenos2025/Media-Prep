# Changelog

All notable changes to this project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- Copyright attribution set to GRC Digital; NOTICE records AI editing
  assistance via Cursor, Codex, and WorkBuddy

### Added

- README demo section: unattended crop/compress flow diagrams plus
  before/after, batch-summary, and contact-sheet screenshots under `assets/`
- Open-source packaging inspired by
  [Skill Self-Check](https://github.com/xenos2025/Skill-Self-Check):
  LICENSE (MIT), NOTICE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, SUPPORT,
  PRIVACY, AGENTS, CHANGELOG, TODO, plugin.json, installers, GitHub templates,
  and CI smoke workflow
- Project home for the former personal `media-prep-workbench` skill under
  `skill/media-prep-workbench/`
- Installable CLI entry via `src/media_prep` (`python -m media_prep`)
- `--profile shopify|generic` on `process-images` / `process-videos`
- Generality upgrade notes in `docs/generality-upgrade.md`

## [0.1.0] - 2026-08-07

### Added

- Initial workbench capability set ported from the personal skill:
  inspect/process images and videos, trim video, name maps, focus maps,
  contact sheets, SHA-256 duplicate skip, storefront presets
