# Distribution smoke check

Run this only when packaging or delivering the tool. The current CLI already supports `--profile`; verify its actual help rather than repeating an old missing-option finding.

1. Record source revision/dirty state, Python/OS, installed Pillow and any required video executables. Compare documented commands and flags with the packaged CLI's `--help` and each used subcommand's help.
2. Build the final archive using an explicit allowlist of distributable code, requirements and skill documentation. Exclude inputs, customer names, logs, caches, credentials, local environments and repository metadata. Hash the archive.
3. Extract that exact archive into a new independent directory. Create synthetic temporary images; run inspect-images and process-images using documented flags, including the selected profile. Do not install dependencies silently. Missing dependencies are an environment result.
4. Compare original hashes, output counts/formats/dimensions and the generated report; inspect the contact sheet. Verify source images stayed unchanged. Record archive hash, commands, return codes and dependency limitations outside the distributable. Done when the extracted artifact passes or the precise blocker is reported.
