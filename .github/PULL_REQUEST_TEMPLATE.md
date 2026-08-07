## Summary

<!-- Why this change exists -->

## Type

- [ ] Skill / CLI behavior (`skill/media-prep-workbench/`)
- [ ] Installable entry (`src/media_prep/`)
- [ ] Docs / OSS packaging
- [ ] Installer / plugin metadata
- [ ] Tests / CI

## Test plan

- [ ] `python -m pip install -e .`
- [ ] `python -m media_prep -h`
- [ ] `python -m media_prep process-images -h` (shows `--profile`)
- [ ] `python -m unittest discover tests -v`
- [ ] Installer smoke (if installers changed):
      `./install.ps1 -Project <temp>` or `./install.sh --project <temp>`
- [ ] CHANGELOG `[Unreleased]` updated when user-visible

## Notes

<!-- Extra context for reviewers -->
