# Storefront Media Presets

Use these defaults unless the project or user gives stricter requirements.

## Shopify Media Compatibility (verified)

These are Shopify's own product-media limits and recommendations (Shopify Help Center + shopify.dev). The processing defaults below are tuned to land inside them so uploads succeed and re-processing stays clean.

- Images: accepted JPEG / PNG / WebP / HEIC / GIF; max 20 MB and ~20-25 MP (up to 5000x5000); recommended 2048x2048 square (1:1); aspect ratio must be within 100:1 and 1:100; zoom needs roughly >=1600 px on the long edge.
- Videos: accepted MP4 / MOV / WebM; max 1 GB, max 10 minutes, 100-4096 px, <=120 fps; codec H.264 (AVC) + audio AAC/MP3/Opus; recommended aspect ratios 16:9, 9:16, 4:3, 3:4, 1:1; recommended resolutions 480p/720p/1080p/2160p; supported color spaces Rec.601/709/2020.
- Shopify ALWAYS re-transcodes uploaded video into its own 480p/720p/1080p HLS + MP4 renditions. You cannot skip this step. The goal of local prep is a clean, already-compatible master (H.264, `yuv420p`, Rec.709 SDR, even dimensions, `+faststart`, within limits) so Shopify's transcode is fast and does not wash out color or fail. HDR (HLG/PQ, BT.2020) masters are the main cause of color shifts and failed processing.

## Images

- Output format: JPEG for photos and product images (`--format jpg`, default). Use WebP only when explicitly requested (`--format webp`); Shopify also auto-serves WebP to supporting browsers, so JPEG masters are fine. The quality/size-target loop applies to both.
- Long edge: 2048 px for product/listing images (matches Shopify's square recommendation and keeps zoom sharp); 1600 px for lightweight blog/support images. The tool warns when an output falls below 1600 px because Shopify zoom degrades.
- Aspect ratio: `--aspect none` (default) preserves the source ratio. Use `--aspect 1:1` (or `4:5` for portrait) with `--fit pad` (default, white pad via `--pad-color`) to give a catalog a consistent Shopify-friendly ratio without cropping product edges; use `--fit cover` only when center-cropping is acceptable.
- JPEG quality: start at 84 and reduce toward 74 only to hit a size target.
- Target size: 600 KB to 1.1 MB per image for most Shopify storefront uploads.
- Metadata: strip EXIF by default.
- QA: create a contact sheet and CSV map with source file, output file, dimensions, bytes, duplicate status, and compression ratio.

## Image Enhancement

Use deterministic correction, not creative recoloring.

- `dark`: gamma 0.92, autocontrast cutoff 0.35, brightness 1.04, contrast 1.11, color 1.06, sharpness 1.04.
- `medium`: gamma 0.93, autocontrast cutoff 0.28, brightness 1.04, contrast 1.10, color 1.06, sharpness 1.05.
- `pastel`: gamma 0.94, autocontrast cutoff 0.22, brightness 1.045, contrast 1.10, color 1.07, sharpness 1.06.
- `texture-safe`: luminance-only gamma 0.97, autocontrast cutoff 0.12, contrast 1.08, unsharp mask radius 1.0 / percent 80 / threshold 3. Chroma is preserved by processing the Y channel only; use for fabric weave, pile, jacquard, white walls, cosmetics, food, art, and other color-critical media where texture needs clarity but colorway must not drift.

Color fidelity default: enhancement is opt-in and `--enhance none` is the default, so runs stay color-faithful unless the user asks otherwise. For fabric, textile, cosmetics, food, art, or other color-sensitive products, keep `none` or use `texture-safe`; use RGB presets (`auto`, `dark`, `medium`, `pastel`) only after a proof image is accepted. Never treat auto enhancement as free: RGB autocontrast, color +6-7%, and added sharpness can shift dusty pink, white, pastel, neutral wall, and other subtle colorways. Report that manual color review remains necessary for these categories.

## Videos

- Output format: MP4 (H.264 via `libx264`, `yuv420p`, `+faststart`). This is the Shopify-recommended master container/codec.
- Color: convert to Rec.709 SDR by default. `process-videos` auto-detects HDR (HLG `arib-std-b67`, PQ `smpte2084`) and BT.2020 sources from `ffprobe` and tonemaps them to Rec.709 (zscale+tonemap when available, `colorspace` fallback otherwise), then tags the output `bt709`. This prevents the washed-out / over-saturated result Shopify produces when it transcodes an HDR master. Use `--keep-hdr` only when you deliberately want to preserve the source color.
- Long edge: 1280 px (720p) by default for product media; use 1920 px (1080p) when the user needs hero video quality. Both are Shopify-recommended resolution buckets. Output is always forced to even dimensions (required by `yuv420p` / H.264).
- Aspect ratio: `--aspect none` (default) preserves the source ratio. Use `--aspect` with a Shopify-recommended ratio (`16:9`, `9:16`, `4:3`, `3:4`, `1:1`) to pad (letterbox/pillarbox via `--pad-color`, default white) to a consistent gallery ratio.
- CRF: 28 for compact storefront media, 24 to 26 for higher quality, 30 to 32 for preview/thumbnail clips.
- FPS: keep source FPS up to 30; reduce higher-FPS sources to 30 for storefront media (Shopify supports 25/30/60).
- Duration/size: keep under Shopify's 10-minute and 1 GB limits; the tool warns when an output exceeds 10 minutes so you trim before upload.
- Audio: remove by default for product and factory clips. Preserve only when sound is part of the content.
- Metadata: strip by default.
- QA: run `ffprobe`, generate contact sheets, and write CSV/JSON summaries. The video map records source vs output color and whether HDR/gamut conversion ran.

## Trimming And Cropping

- Trim by explicit start and duration or end time.
- Preserve source file and write a new clip.
- For crop/format conversion, inspect the source orientation first. Do not crop meaningful product edges without user approval.
- For reels or social variants, use project-specific specs from the active task.
