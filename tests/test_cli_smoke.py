"""Smoke tests for the media-prep CLI entry and skill script."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skill" / "media-prep-workbench" / "scripts" / "media_prep.py"


class CliSmokeTests(unittest.TestCase):
    def test_module_help(self) -> None:
        cp = subprocess.run(
            [sys.executable, "-m", "media_prep", "-h"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("inspect-images", cp.stdout)

    def test_process_images_has_profile(self) -> None:
        cp = subprocess.run(
            [sys.executable, "-m", "media_prep", "process-images", "-h"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("--profile", cp.stdout)
        self.assertIn("shopify", cp.stdout)
        self.assertIn("generic", cp.stdout)

    def test_skill_script_help(self) -> None:
        self.assertTrue(SCRIPT.is_file(), f"missing {SCRIPT}")
        cp = subprocess.run(
            [sys.executable, str(SCRIPT), "-h"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("process-videos", cp.stdout)


if __name__ == "__main__":
    unittest.main()
