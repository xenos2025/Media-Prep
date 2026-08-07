#!/usr/bin/env bash
# Install the media-prep-workbench Agent Skill into a Cursor skills directory
# (user global by default) or a project.
# Usage:
#   ./install.sh
#   ./install.sh --project .
#   ./install.sh --dest "$HOME/.cursor/skills/media-prep-workbench"
#   ./install.sh --force

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST=""
PROJECT=""
FORCE=0
SKILLS=(media-prep-workbench)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest) DEST="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --skills) IFS=',' read -r -a SKILLS <<< "$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    -h|--help)
      sed -n '2,8p' "$0"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -n "$DEST" ]]; then
  SKILLS=("${SKILLS[0]}")
fi

if [[ -z "$DEST" && -n "$PROJECT" ]]; then
  BASE="$(cd "$PROJECT" && pwd)/.cursor/skills"
elif [[ -z "$DEST" ]]; then
  BASE="${HOME}/.cursor/skills"
fi

for SKILL in "${SKILLS[@]}"; do
  SRC="$ROOT/skill/$SKILL"
  if [[ ! -d "$SRC" ]]; then
    echo "Missing skill/$SKILL at $SRC" >&2
    exit 1
  fi

  if [[ -n "$DEST" ]]; then
    TARGET="$DEST"
  else
    TARGET="$BASE/$SKILL"
  fi

  TARGET_PARENT="$(dirname "$TARGET")"
  mkdir -p "$TARGET_PARENT"
  TARGET_PARENT_ABS="$(cd "$TARGET_PARENT" && pwd -P)"
  TARGET_ABS="$TARGET_PARENT_ABS/$(basename "$TARGET")"
  HOME_ABS="$(cd "$HOME" && pwd -P)"

  if [[ "$(basename "$TARGET_ABS")" != "$SKILL" ]]; then
    echo "Install target must end with the skill name '$SKILL': $TARGET_ABS" >&2
    exit 1
  fi
  if [[ "$TARGET_ABS" == "$HOME_ABS" || "$TARGET_ABS" == "$ROOT" ]]; then
    echo "Unsafe install target: $TARGET_ABS" >&2
    exit 1
  fi
  if [[ "$TARGET_PARENT_ABS" == "/" ]]; then
    echo "Refusing to install directly under the filesystem root: $TARGET_ABS" >&2
    exit 1
  fi
  TARGET="$TARGET_ABS"

  if [[ -e "$TARGET" && "$FORCE" -ne 1 ]]; then
    echo "Destination exists: $TARGET (pass --force to overwrite)" >&2
    exit 1
  fi
  rm -rf "$TARGET"
  cp -R "$SRC" "$TARGET"
  echo "Installed $SKILL -> $TARGET"
done

echo "Requires Python 3.10+, Pillow, and FFmpeg on PATH for video. Try:"
echo "  python -m pip install -e \"$ROOT\""
echo "  python -m media_prep inspect-images --src path/to/images --out path/to/out/inspect-images"
echo "  python \"\$HOME/.cursor/skills/media-prep-workbench/scripts/media_prep.py\" -h"
