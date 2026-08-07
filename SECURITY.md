# Security Policy

Media Prep is a local media-preparation workbench: an Agent Skill plus a
Python CLI that reads source folders and writes isolated output folders.
This document covers vulnerability reporting and trust boundaries.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security findings.**

1. Prefer a GitHub Security Advisory on this repository, or contact the
   repository owner privately (see [SUPPORT.md](SUPPORT.md)).
2. Include a minimal reproducer, affected path, and suggested severity.
3. Allow at least 14 days for a coordinated fix before public disclosure
   (faster for actively exploitable issues).

You should receive an acknowledgement within 7 days.

## Supported Versions

Only the latest commit on `main` (and tagged releases when published) receives
security fixes.

## In Scope

- Python under `skill/media-prep-workbench/scripts/` and `src/media_prep/`
- Installers: `install.ps1`, `install.sh`
- Skill markdown that can be loaded as LLM instructions (`SKILL.md`)
- Path handling that could write outside an intended output directory
- Accidental secret exposure in examples or docs

## Out of Scope

- Vulnerabilities in Cursor, Claude Code, Codex, or host LLM platforms
- FFmpeg / Pillow upstream bugs (report upstream; we track workarounds here)
- Shopify Admin, theme, or third-party store APIs (this tool does not upload)
- Social-engineering the user into pasting store tokens into chat

## Trust boundaries

- The CLI **reads** source media and **writes** to a caller-chosen `--out`
  directory. Defaults prefer a new `media-prep-workbench\` run folder under
  the source tree; originals stay read-only unless the user explicitly asks
  otherwise.
- Metadata is stripped from generated media by default.
- Installers **copy** files into `~/.cursor/skills` or `.cursor/skills` —
  review the destination before `-Force` / `--force`.
- Do not put live customer PII, store tokens, or production exports in a
  public fork.
