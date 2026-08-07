"""Console entry that runs the skill-bundled media_prep.py script."""
from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    script = (
        Path(__file__).resolve().parents[2]
        / "skill"
        / "media-prep-workbench"
        / "scripts"
        / "media_prep.py"
    )
    if not script.is_file():
        raise SystemExit(f"media_prep script not found: {script}")
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
