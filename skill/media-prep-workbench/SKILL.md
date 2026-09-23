---
name: media-prep-workbench
description: Batch prepare storefront media assets for Shopify or independent sites. Use when inspecting, renaming, deduplicating, compressing, color-correcting, enhancing, trimming, cropping, transcoding, or QA-ing product images, listing photos, lifestyle images, product videos, factory clips, reels, MP4s, JPGs, PNGs, WebPs, or upload-ready media folders.
---

# Media Prep Workbench

## Project home

Canonical package lives in the `media-prep` repo at `skill/media-prep-workbench/`. Prefer running scripts from that tree (or the installable `media-prep` CLI). Personal skill copies under `~/.codex/skills` or `~/.cursor/skills` should sync from the repo, not diverge.

`<skill-root>` below means this skill directory (repo path: `<repo>/skill/media-prep-workbench`).

## Scope

Use this skill as the execution layer for local storefront media preparation. It is project-neutral: keep client names, product taxonomy, SEO terms, output folders, and naming decisions in the active project or task notes, not in this skill.

Default to local-only file work. Do not upload to Shopify, change product media, edit theme files, delete originals, or overwrite source folders unless the user explicitly scopes that work and the active Shopify skill or project rules allow it.

Target profile: `process-images` / `process-videos` default to `--profile shopify` (platform QA warnings). Use `--profile generic` for non-Shopify storefronts when you want the same encode path without Shopify-specific warn copy.

## Output Root

When the user does not specify an output path, keep media-prep outputs under the original source directory by creating a new isolated folder:

```text
<source-folder>\media-prep-workbench\<task-slug>-<timestamp>\
```

For mixed media or multiple source folders, create the run folder under the specific source folder being processed, or under the nearest common source parent when that is clearer. Use subfolders by operation so outputs do not mix with originals:

```text
inspect-images\
inspect-videos\
processed-images\
processed-videos\
clips\
reports\
maps\
```

Keep source files read-only by default. Do not write processed media directly beside originals, and exclude the `media-prep-workbench\` run folder from future source scans unless the user explicitly wants to reprocess previous outputs.

## Workflow

1. Confirm source folder, target use, and whether the task is image, video, or mixed media.
2. Inspect before processing:
   - Run `scripts/media_prep.py inspect-images` for images.
   - Run `scripts/media_prep.py inspect-videos` for videos.
   - Review contact sheets before final naming when content-based names are needed.
3. Create a CSV name map when filenames need content-aware English names. Use columns `index,output_stem` (source order) and/or `source_file,output_stem` (exact filename); omit extensions in `output_stem`. Prefer the `source_file` key when the source folder may change between inspect and process, since index-based rows shift if files are added or removed.
4. Process into a new output folder. Preserve originals by default.
5. Verify counts, skipped duplicates, failed rows, total size reduction, contact sheets, and a CSV or JSON summary.
6. Record project-specific decisions in the project log when the surrounding project requires it.

## Script Quick Start

On Windows, path summaries print as UTF-8 (the script sets the console code page when possible). If a terminal still shows mojibake for Chinese or other non-ASCII folder names, run `$env:PYTHONIOENCODING='utf-8'` in PowerShell before invoking the script, or use PowerShell 7+.

Image inspection:

```powershell
python <skill-root>\scripts\media_prep.py inspect-images --src "E:\path\images" --out "E:\path\images\media-prep-workbench\<task-slug>-<timestamp>\inspect-images"
```

Image compression or enhancement:

```powershell
python <skill-root>\scripts\media_prep.py process-images --src "E:\path\images" --out "E:\path\images\media-prep-workbench\<task-slug>-<timestamp>\processed-images" --name-map names.csv --enhance auto
```

Color-sensitive fabric texture cleanup:

```powershell
python <skill-root>\scripts\media_prep.py process-images --src "E:\path\images" --out "E:\path\images\media-prep-workbench\<task-slug>-<timestamp>\processed-images" --enhance texture-safe
```

Shopify-consistent square images (pad to 1:1 on white, keep color faithful):

```powershell
python <skill-root>\scripts\media_prep.py process-images --src "E:\path\images" --out "E:\path\images\media-prep-workbench\<task-slug>-<timestamp>\processed-images" --aspect 1:1 --fit pad --pad-color white
```

Rotate landscape photos 90° to portrait (4:3 landscape becomes 3:4; portrait unchanged):

```powershell
python <skill-root>\scripts\media_prep.py process-images --src "E:\path\images" --out "E:\path\images\media-prep-workbench\<task-slug>-<timestamp>\processed-images" --rotate-landscape cw --enhance none
```

Cover-crop to 3:4 with a left-weighted focal point (keeps off-center products in frame):

```powershell
python <skill-root>\scripts\media_prep.py process-images --src "E:\path\images" --out "E:\path\images\media-prep-workbench\<task-slug>-<timestamp>\processed-images" --aspect 3:4 --fit cover --focus-x 0.25 --enhance none
```

Per-image focal points via CSV (`source_file,focus_x,focus_y`; values 0..1, default center is 0.5):

```powershell
python <skill-root>\scripts\media_prep.py process-images --src "E:\path\images" --out "E:\path\images\media-prep-workbench\<task-slug>-<timestamp>\processed-images" --aspect 3:4 --fit cover --focus-map maps\focus-map.csv --enhance none
```

After any `--fit cover` batch, review `image-process-contact-sheet.jpg` before upload. Collages, ultra-wide panoramas, and multi-subject frames often need per-image focal tuning or `--fit pad` instead of a single global focal point.

Video inspection:

```powershell
python <skill-root>\scripts\media_prep.py inspect-videos --src "E:\path\video" --out "E:\path\video\media-prep-workbench\<task-slug>-<timestamp>\inspect-videos"
```

Video compression and rename (auto HDR->Rec.709 SDR for Shopify):

```powershell
python <skill-root>\scripts\media_prep.py process-videos --src "E:\path\video" --out "E:\path\video\media-prep-workbench\<task-slug>-<timestamp>\processed-videos" --name-map names.csv
```

Optional: pad or center-crop video to a Shopify-recommended aspect ratio (16:9, 9:16, 4:3, 3:4, 1:1):

```powershell
python <skill-root>\scripts\media_prep.py process-videos --src "E:\path\video" --out "E:\path\video\media-prep-workbench\<task-slug>-<timestamp>\processed-videos" --aspect 3:4 --fit cover
```

`--fit pad` (default) letterboxes; `--fit cover` center-crops to the target ratio with no bars.

Basic clipping:

```powershell
python <skill-root>\scripts\media_prep.py trim-video --input "E:\path\video\source.mp4" --output "E:\path\video\media-prep-workbench\<task-slug>-<timestamp>\clips\clip.mp4" --start 00:00:03 --duration 8
```

## Naming Rules

Use lowercase English slugs for upload-ready files. Prefer buyer-visible material, pattern, color, use, and shot type:

`pastel-floral-jacquard-fabric-rolls-closeup`

Avoid hash-only names, raw WeChat names, client-only shorthand, and unverified product claims. Use project-local terms for brand-specific collection names, SKUs, material claims, or SEO priorities.

## Defaults

Use `references/storefront-media-presets.md` for default dimensions, video settings, enhancement presets, QA checks, verified Shopify media limits, and when to override them.

Enhancement is opt-in: `process-images` defaults to `--enhance none` (color-faithful) and `--format jpg`. Only enable `--enhance auto|dark|medium|pastel` when the user accepts tone/color adjustment, and keep `none` for color-sensitive products (fabric, textile, cosmetics, food, art) unless a single-image trial is approved. For fabric or textile photos where the user wants weave/pile texture clearer without shifting the colorway, use `--enhance texture-safe`: it adjusts only luminance contrast and unsharp masking while preserving chroma channels.

Shopify compatibility is built into the defaults so uploads are not re-processed with surprises:

- Images output at 2048 px long edge (Shopify's square recommendation); `--aspect 1:1|4:5|...` pads to a consistent, catalog-friendly ratio (`--fit pad` on white by default, `--fit cover` to crop). With `--fit cover`, use `--focus-x` / `--focus-y` (0..1, default 0.5 center) or a `--focus-map` CSV keyed by `source_file` to keep off-center products in frame. Review contact sheets after cover crops, especially for collages and ultra-wide images. A warning fires when an output drops below 1600 px because Shopify zoom degrades.
- Videos output as H.264 / `yuv420p` / `+faststart` MP4 with even dimensions, and are auto-converted from HDR (HLG/PQ) or BT.2020 to Rec.709 SDR unless `--keep-hdr` is set. Shopify still re-transcodes every uploaded video into its own renditions; a clean Rec.709 master only makes that transcode fast, color-accurate, and failure-free. Use `--aspect` to pad to a Shopify-recommended ratio (16:9, 9:16, 4:3, 3:4, 1:1).

## Safety

- Preserve source files unless the user explicitly asks to overwrite or delete.
- Write outputs to a new `media-prep-workbench\` run folder inside the source directory by default.
- Detect exact duplicates by SHA-256 and write skipped duplicate reports.
- Generate contact sheets and maps so a human can audit content and filenames.
- Strip metadata from generated media unless preservation is requested.
- Remove audio from product videos by default for storefront media; preserve it only when user explicitly needs sound.
- Treat AI image generation, background replacement, retouching that changes product appearance, or color changes beyond correction as separate creative work requiring explicit approval.
- Do not batch RGB autocontrast presets on pink, white, pastel, fabric, cosmetic, food, or other color-critical media without a proof image; prefer `none` or `texture-safe`.

When preparing a distributable media-prep archive, Read [this workflow](references/release-smoke.md) before preparing the change. Done when its scoped evidence and verification record are complete.
