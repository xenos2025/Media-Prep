#!/usr/bin/env python3
"""Project-neutral storefront media preparation helper."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re, shutil, subprocess, sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

def configure_console_utf8() -> None:
    """Best-effort UTF-8 stdout/stderr on Windows so path summaries stay readable."""
    if sys.platform != 'win32':
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except (AttributeError, OSError, ValueError):
            pass
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff'}
VIDEO_EXTS = {'.mp4', '.mov', '.m4v', '.webm'}
PRESETS = {
    'dark': {'gamma': .92, 'cutoff': .35, 'brightness': 1.04, 'contrast': 1.11, 'color': 1.06, 'sharpness': 1.04},
    'medium': {'gamma': .93, 'cutoff': .28, 'brightness': 1.04, 'contrast': 1.10, 'color': 1.06, 'sharpness': 1.05},
    'pastel': {'gamma': .94, 'cutoff': .22, 'brightness': 1.045, 'contrast': 1.10, 'color': 1.07, 'sharpness': 1.06},
    'texture-safe': {'mode': 'luminance', 'gamma': .97, 'cutoff': .12, 'brightness': 1.0, 'contrast': 1.08, 'unsharp_radius': 1.0, 'unsharp_percent': 80, 'unsharp_threshold': 3},
}

try:
    from mozjpeg_lossless_optimization import optimize_jpeg as _mozjpeg_opt
    HAS_MOZJPEG = True
except ImportError:
    HAS_MOZJPEG = False

def need_pil():
    try:
        import PIL  # noqa
    except Exception as exc:
        raise SystemExit('Pillow is required: ' + str(exc))

def need_ffmpeg():
    missing = [t for t in ('ffmpeg', 'ffprobe') if not shutil.which(t)]
    if missing:
        raise SystemExit('Required tool(s) not found on PATH: ' + ', '.join(missing) + '. Install FFmpeg (ffmpeg + ffprobe).')

def load_rgb_on_white(im):
    """Return an RGB image, compositing any alpha onto white (not black)."""
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(im)
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
        im = im.convert('RGBA')
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    return im.convert('RGB')

# Storefront / Shopify-compatible media targets. Shopify Help Center + shopify.dev:
# images 1:1 2048px preferred; video H.264/AAC MP4, SDR Rec.709, <=4096px /
# <=10min / <=1GB, recommended ratios 16:9/9:16/4:3/3:4/1:1. Shopify ALWAYS
# re-transcodes uploaded video; local prep aims for a clean master. These limits
# are applied when --profile shopify (default); --profile generic keeps the same
# encode path but softens platform-specific warnings.
ASPECT_CHOICES = ['none', '1:1', '4:5', '5:4', '4:3', '3:4', '16:9', '9:16']
PROFILE_CHOICES = ['shopify', 'generic']
SHOPIFY_MAX_VIDEO_EDGE = 4096
SHOPIFY_MAX_VIDEO_SECONDS = 600
SHOPIFY_ZOOM_MIN_EDGE = 1600

def normalize_profile(value: Optional[str]) -> str:
    name = (value or 'shopify').strip().lower()
    if name not in PROFILE_CHOICES:
        raise SystemExit(f'Invalid --profile {value!r}. Use: {", ".join(PROFILE_CHOICES)}.')
    return name

_FILTERS_CACHE = None
def has_filter(name: str) -> bool:
    global _FILTERS_CACHE
    if _FILTERS_CACHE is None:
        cp = run(['ffmpeg', '-hide_banner', '-filters'])
        _FILTERS_CACHE = cp.stdout if cp.returncode == 0 else ''
    return re.search(r'\b' + re.escape(name) + r'\b', _FILTERS_CACHE) is not None

def parse_aspect(value: Optional[str]):
    if not value or value == 'none':
        return None
    m = re.match(r'^(\d+):(\d+)$', value.strip())
    if not m or int(m.group(1)) == 0 or int(m.group(2)) == 0:
        raise SystemExit(f'Invalid --aspect {value!r}. Use W:H such as 1:1, 4:5, 16:9, or none.')
    return int(m.group(1)), int(m.group(2))

def pad_rgb(value: Optional[str]):
    name = (value or 'white').strip().lower()
    if name == 'white': return (255, 255, 255)
    if name == 'black': return (0, 0, 0)
    m = re.match(r'^#?([0-9a-f]{6})$', name)
    if m:
        h = m.group(1); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    raise SystemExit(f'Invalid --pad-color {value!r}. Use white, black, or #rrggbb.')

def parse_focus(value: Optional[float], name: str) -> float:
    if value is None:
        return 0.5
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise SystemExit(f'Invalid {name} {value!r}. Use a number between 0 and 1.')
    if v < 0 or v > 1:
        raise SystemExit(f'Invalid {name} {value!r}. Must be between 0 and 1 (0=left/top, 1=right/bottom, 0.5=center).')
    return v

def fit_aspect_image(img, aspect, mode, pad, focus_x: float = 0.5, focus_y: float = 0.5):
    """Normalize an image to a target aspect ratio by padding (default) or cover-cropping."""
    if not aspect:
        return img
    from PIL import Image
    aw, ah = aspect; target = aw / ah; w, h = img.size; cur = w / h
    fx, fy = parse_focus(focus_x, 'focus_x'), parse_focus(focus_y, 'focus_y')
    if mode == 'cover':
        if cur > target:
            nw = round(h * target); x = max(0, min(round(fx * w - nw / 2), w - nw)); return img.crop((x, 0, x + nw, h))
        nh = round(w / target); y = max(0, min(round(fy * h - nh / 2), h - nh)); return img.crop((0, y, w, y + nh))
    if cur > target:
        nw, nh = w, round(w / target)
    else:
        nh, nw = h, round(h * target)
    canvas = Image.new('RGB', (nw, nh), pad); canvas.paste(img, ((nw - w) // 2, (nh - h) // 2)); return canvas

def rotate_landscape(img, direction: Optional[str]):
    """Rotate landscape (width > height) images 90° to portrait. Portrait/square unchanged.

    direction: 'cw' (clockwise) or 'ccw' (counter-clockwise). Returns (image, applied_label).
    """
    if not direction or direction == 'none':
        return img, 'none'
    w, h = img.size
    if w <= h:
        return img, 'none'
    from PIL import Image
    # PIL Transpose.ROTATE_90 = 90° CCW; ROTATE_270 = 90° CW.
    if direction == 'cw':
        return img.transpose(Image.Transpose.ROTATE_270), 'cw'
    if direction == 'ccw':
        return img.transpose(Image.Transpose.ROTATE_90), 'ccw'
    raise SystemExit(f'Invalid --rotate-landscape {direction!r}. Use none, cw, or ccw.')

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def slugify(text: str) -> str:
    text = re.sub(r'[^a-zA-Z0-9]+', '-', text.lower()).strip('-')
    return re.sub(r'-+', '-', text) or 'media'

def files(src: Path, exts: set[str]) -> List[Path]:
    return sorted([p for p in src.iterdir() if p.is_file() and p.suffix.lower() in exts], key=lambda p: p.name.lower())

def read_names(path: Optional[str]) -> Tuple[Dict[int, str], Dict[str, str]]:
    """Return (by_index, by_source_filename). A name map may key rows by numeric
    `index` (source order) and/or by `source_file` (exact filename). Filename
    match is preferred at process time because it survives source-folder churn."""
    by_index: Dict[int, str] = {}
    by_name: Dict[str, str] = {}
    if not path:
        return by_index, by_name
    with Path(path).open('r', encoding='utf-8-sig', newline='') as f:
        for lineno, row in enumerate(csv.DictReader(f), start=2):
            stem = (row.get('output_stem') or '').strip()
            if not stem:
                continue
            slug = slugify(stem)
            src = (row.get('source_file') or '').strip()
            if src:
                by_name[src.lower()] = slug
            idx_raw = (row.get('index') or '').strip()
            if idx_raw:
                try:
                    by_index[int(idx_raw)] = slug
                except ValueError:
                    print(f'[WARN] name-map row {lineno}: non-numeric index {idx_raw!r}, skipped')
    return by_index, by_name

def read_focus_map(path: Optional[str]) -> Dict[str, Tuple[float, float]]:
    """Return per-source_file (focus_x, focus_y) pairs for cover crops (0..1)."""
    by_name: Dict[str, Tuple[float, float]] = {}
    if not path:
        return by_name
    with Path(path).open('r', encoding='utf-8-sig', newline='') as f:
        for lineno, row in enumerate(csv.DictReader(f), start=2):
            src = (row.get('source_file') or '').strip()
            if not src:
                print(f'[WARN] focus-map row {lineno}: missing source_file, skipped')
                continue
            fx = parse_focus(row.get('focus_x'), f'focus-map row {lineno} focus_x')
            fy = parse_focus(row.get('focus_y'), f'focus-map row {lineno} focus_y')
            by_name[src.lower()] = (fx, fy)
    return by_name

def write_csv(path: Path, rows: List[dict], fields: List[str]):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)

def font(size=13, bold=False):
    from PIL import ImageFont
    for name in (('arialbd.ttf' if bold else 'arial.ttf'), ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')):
        try: return ImageFont.truetype(name, size)
        except Exception: pass
    return ImageFont.load_default()

def contact_sheet(items: List[dict], output: Path, title: str):
    need_pil(); from PIL import Image, ImageDraw, ImageOps
    cols, tw, th, lh = 4, 300, 220, 86
    rows = max(1, math.ceil(len(items) / cols))
    sheet = Image.new('RGB', (cols * tw, rows * (th + lh) + 44), 'white')
    draw = ImageDraw.Draw(sheet); draw.text((12, 12), title, fill=(20,20,20), font=font(18, True))
    for pos, item in enumerate(items):
        x, y = (pos % cols) * tw, 44 + (pos // cols) * (th + lh)
        draw.rectangle([x, y, x + tw - 1, y + th + lh - 1], outline=(220,220,220))
        p = Path(item.get('path', ''))
        if p.exists():
            with Image.open(p) as im:
                im = load_rgb_on_white(im); im.thumbnail((tw - 18, th - 18), Image.Resampling.LANCZOS)
                sheet.paste(im, (x + (tw - im.width)//2, y + 8 + (th - 18 - im.height)//2))
        draw.text((x+8, y+th+4), item.get('label','')[:38], fill=(0,0,0), font=font(14, True))
        draw.text((x+8, y+th+26), item.get('line1','')[:44], fill=(70,70,70), font=font())
        draw.text((x+8, y+th+46), item.get('line2','')[:44], fill=(70,70,70), font=font())
    sheet.save(output, 'JPEG', quality=88, optimize=True)

def luma(img) -> dict:
    g = img.convert('L'); hist = g.histogram(); total = sum(hist) or 1
    mean = sum(i*c for i,c in enumerate(hist)) / total; acc = 0; p05 = p50 = p95 = 0
    for i,c in enumerate(hist):
        acc += c
        if not p05 and acc >= total * .05: p05 = i
        if not p50 and acc >= total * .50: p50 = i
        if not p95 and acc >= total * .95: p95 = i; break
    return {'mean_luma': round(mean, 2), 'p05': p05, 'p50': p50, 'p95': p95}

def choose_preset(stats):
    if stats['mean_luma'] < 105 or stats['p50'] < 95: return 'dark'
    if stats['mean_luma'] < 126 or stats['p50'] < 122: return 'medium'
    return 'pastel'

def enhance(img, name):
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    p = PRESETS[name]; lut = [round(255 * ((i/255) ** p['gamma'])) for i in range(256)]
    if p.get('mode') == 'luminance':
        y, cb, cr = img.convert('YCbCr').split()
        y = y.point(lut)
        y = ImageOps.autocontrast(y, cutoff=p['cutoff'])
        y = ImageEnhance.Brightness(y).enhance(p['brightness'])
        y = ImageEnhance.Contrast(y).enhance(p['contrast'])
        y = y.filter(ImageFilter.UnsharpMask(radius=p['unsharp_radius'], percent=p['unsharp_percent'], threshold=p['unsharp_threshold']))
        return Image.merge('YCbCr', (y, cb, cr)).convert('RGB')
    img = img.point(lut * 3); img = ImageOps.autocontrast(img, cutoff=p['cutoff'])
    img = ImageEnhance.Brightness(img).enhance(p['brightness']); img = ImageEnhance.Contrast(img).enhance(p['contrast'])
    img = ImageEnhance.Color(img).enhance(p['color']); img = ImageEnhance.Sharpness(img).enhance(p['sharpness'])
    return img

def inspect_images(args):
    need_pil(); from PIL import Image, ImageOps
    src, out = Path(args.src), Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rows, items = [], []
    for idx,p in enumerate(files(src, IMAGE_EXTS), 1):
        with Image.open(p) as im:
            im = ImageOps.exif_transpose(im); w,h = im.size; mode = im.mode
        row = {'index': idx, 'name': p.name, 'bytes': p.stat().st_size, 'mb': round(p.stat().st_size/1048576,2), 'width': w, 'height': h, 'mode': mode, 'sha256': sha256_file(p)}
        rows.append(row); items.append({'path': str(p), 'label': f'{idx:02d} {p.name}', 'line1': f'{w}x{h} {row["mb"]}MB', 'line2': mode})
    fields = ['index','name','bytes','mb','width','height','mode','sha256']; write_csv(out/'source-image-metadata.csv', rows, fields)
    (out/'source-image-metadata.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    contact_sheet(items, out/'source-image-contact-sheet.jpg', 'Source images contact sheet')
    print(f'images={len(rows)} out={out}')

def process_images(args):
    need_pil(); from PIL import Image
    src, out = Path(args.src), Path(args.out); out.mkdir(parents=True, exist_ok=args.exist_ok)
    names_idx, names_name = read_names(args.name_map); seen, created, skipped = {}, [], []
    target = args.target_kb * 1024
    flist = files(src, IMAGE_EXTS); pad = max(2, len(str(len(flist))))
    fmt = args.format; ext = 'jpg' if fmt == 'jpg' else 'webp'
    aspect = parse_aspect(args.aspect); pad_color = pad_rgb(args.pad_color)
    rotate_dir = args.rotate_landscape
    default_fx = parse_focus(args.focus_x, '--focus-x')
    default_fy = parse_focus(args.focus_y, '--focus-y')
    focus_by_name = read_focus_map(args.focus_map)
    rotated_count = 0
    for idx,p in enumerate(flist, 1):
        digest = sha256_file(p)
        if digest in seen:
            skipped.append({'source_index': idx, 'source_file': p.name, 'duplicate_of_source_index': seen[digest]['source_index'], 'duplicate_of_output_file': seen[digest]['output_file'], 'sha256': digest}); continue
        stem = names_name.get(p.name.lower()) or names_idx.get(idx) or slugify(p.stem); output = out / f'{idx:0{pad}d}-{stem}.{ext}'
        with Image.open(p) as im:
            img = load_rgb_on_white(im); sw,sh = img.size
            img, rotated = rotate_landscape(img, rotate_dir)
            if rotated != 'none':
                rotated_count += 1
            fx, fy = focus_by_name.get(p.name.lower(), (default_fx, default_fy))
            img = fit_aspect_image(img, aspect, args.fit, pad_color, focus_x=fx, focus_y=fy)
            if max(img.size) > args.max_edge: img.thumbnail((args.max_edge,args.max_edge), Image.Resampling.LANCZOS)
            before = luma(img); preset = 'none'
            if args.enhance != 'none': preset = choose_preset(before) if args.enhance == 'auto' else args.enhance; img = enhance(img, preset)
            after = luma(img); q = args.quality
            while True:
                if fmt == 'jpg':
                    img.save(output, 'JPEG', quality=q, optimize=True, progressive=True)
                    if HAS_MOZJPEG:
                        try: _mozjpeg_opt(str(output))
                        except Exception: pass
                else:
                    img.save(output, 'WEBP', quality=q, method=6, exact=1)
                    if output.stat().st_size > p.stat().st_size * 0.95 and q <= args.min_quality + 4:
                        img.save(output, 'WEBP', lossless=True, method=6)
                if output.stat().st_size <= target or q <= args.min_quality: break
                q -= 2
        obytes = output.stat().st_size
        item = {'source_index': idx, 'source_file': p.name, 'output_file': output.name, 'format': ext, 'preset': preset, 'quality': q, 'target_met': ('yes' if obytes <= target else 'no'), 'source_bytes': p.stat().st_size, 'output_bytes': obytes, 'source_dimensions': f'{sw}x{sh}', 'output_dimensions': f'{img.width}x{img.height}', 'compression_ratio': round((1-obytes/p.stat().st_size)*100,1), 'rotated': rotated, 'focus_x': fx if args.fit == 'cover' and aspect else '', 'focus_y': fy if args.fit == 'cover' and aspect else '', 'baseline_p50': before['p50'], 'enhanced_p50': after['p50'], 'sha256': digest, 'path': str(output)}
        created.append(item); seen[digest] = {'source_index': idx, 'output_file': output.name}
    fields = ['source_index','source_file','output_file','format','preset','quality','target_met','source_bytes','output_bytes','source_dimensions','output_dimensions','compression_ratio','rotated','focus_x','focus_y','baseline_p50','enhanced_p50','sha256']
    write_csv(out/'image-process-map.csv', created, fields); write_csv(out/'skipped-duplicate-images.csv', skipped, ['source_index','source_file','duplicate_of_source_index','duplicate_of_output_file','sha256'])
    profile = normalize_profile(getattr(args, 'profile', 'shopify'))
    over = [i for i in created if i['target_met'] == 'no']
    low_zoom = [i for i in created if max(int(i['output_dimensions'].split('x')[0]), int(i['output_dimensions'].split('x')[1])) < SHOPIFY_ZOOM_MIN_EDGE]
    (out/'image-process-summary.json').write_text(json.dumps({'profile': profile, 'created_count': len(created), 'skipped_exact_duplicates': len(skipped), 'over_target_count': len(over), 'below_zoom_min_count': len(low_zoom), 'rotated_landscape_count': rotated_count, 'rotate_landscape': rotate_dir, 'focus_x': default_fx, 'focus_y': default_fy, 'focus_map': args.focus_map or None, 'target_kb': args.target_kb, 'aspect': args.aspect, 'fit': args.fit, 'format': ext, 'created': created, 'skipped': skipped}, ensure_ascii=False, indent=2), encoding='utf-8')
    contact_sheet([{'path': i['path'], 'label': i['output_file'], 'line1': f'{i["output_dimensions"]} {round(i["output_bytes"]/1024)}KB {i["preset"]}', 'line2': f'source #{i["source_index"]:0{pad}d} {i["compression_ratio"]}% rot={i["rotated"]}'} for i in created], out/'image-process-contact-sheet.jpg', 'Processed images contact sheet')
    if over: print(f'[WARN] {len(over)} image(s) still exceed target {args.target_kb}KB at min-quality {args.min_quality}: ' + ', '.join(i['output_file'] for i in over))
    if low_zoom and profile == 'shopify':
        print(f'[WARN] {len(low_zoom)} image(s) below {SHOPIFY_ZOOM_MIN_EDGE}px long edge; Shopify zoom may be limited (recommend 2048px): ' + ', '.join(i['output_file'] for i in low_zoom))
    elif low_zoom and profile == 'generic':
        print(f'[INFO] {len(low_zoom)} image(s) below {SHOPIFY_ZOOM_MIN_EDGE}px long edge: ' + ', '.join(i['output_file'] for i in low_zoom))
    print(f'profile={profile} created={len(created)} skipped={len(skipped)} over_target={len(over)} rotated_landscape={rotated_count} out={out}')

def run(cmd): return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
def ffprobe(p: Path) -> dict:
    cp = run(['ffprobe','-v','error','-print_format','json','-show_format','-show_streams',str(p)])
    if cp.returncode: return {'error': cp.stderr.strip(), 'streams': [], 'format': {}}
    return json.loads(cp.stdout)
def stream(meta, kind): return next((s for s in meta.get('streams', []) if s.get('codec_type') == kind), {})
def fps(rate):
    try:
        if '/' in rate:
            a,b = rate.split('/',1); return float(a)/float(b) if float(b) else 0
        return float(rate)
    except Exception: return 0

def video_rows(src: Path):
    rows = []
    for idx,p in enumerate(files(src, VIDEO_EXTS), 1):
        meta = ffprobe(p); v = stream(meta,'video'); a = stream(meta,'audio'); f = meta.get('format', {})
        dur = float(f.get('duration') or v.get('duration') or 0); rate = fps(v.get('avg_frame_rate') or v.get('r_frame_rate') or '0')
        rows.append({'index': idx, 'name': p.name, 'bytes': p.stat().st_size, 'mb': round(p.stat().st_size/1048576,2), 'duration_sec': round(dur,2), 'width': int(v.get('width') or 0), 'height': int(v.get('height') or 0), 'fps': round(rate,2), 'video_codec': v.get('codec_name',''), 'audio_codec': a.get('codec_name',''), 'color_primaries': v.get('color_primaries',''), 'color_transfer': v.get('color_transfer',''), 'color_space': v.get('color_space',''), 'sha256': sha256_file(p)})
    return rows

def inspect_videos(args):
    need_pil(); need_ffmpeg(); src, out = Path(args.src), Path(args.out); out.mkdir(parents=True, exist_ok=True); thumbs = out/'thumbs'; thumbs.mkdir(exist_ok=True)
    rows = video_rows(src)
    for r in rows:
        ss = max(.2, min(r['duration_sec']*.35, 3.0)) if r['duration_sec'] else .5; thumb = thumbs / f'{r["index"]:03d}.jpg'
        run(['ffmpeg','-hide_banner','-loglevel','error','-ss',f'{ss:.2f}','-i',str(src/r['name']),'-frames:v','1','-vf','scale=360:-2','-y',str(thumb)]); r['thumb'] = str(thumb)
    fields = ['index','name','bytes','mb','duration_sec','width','height','fps','video_codec','audio_codec','color_primaries','color_transfer','color_space','sha256','thumb']; write_csv(out/'source-video-metadata.csv', rows, fields)
    (out/'source-video-metadata.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    contact_sheet([{'path': r['thumb'], 'label': f'{r["index"]:02d} {r["name"]}', 'line1': f'{r["width"]}x{r["height"]} {r["duration_sec"]}s {r["mb"]}MB', 'line2': f'{r["video_codec"]} {r["fps"]}fps'} for r in rows], out/'source-video-contact-sheet.jpg', 'Source videos contact sheet')
    print(f'videos={len(rows)} out={out}')

def process_videos(args):
    need_pil(); need_ffmpeg(); src, out = Path(args.src), Path(args.out); out.mkdir(parents=True, exist_ok=args.exist_ok); thumbs = out/'_qa-thumbs'; thumbs.mkdir(exist_ok=True)
    names_idx, names_name = read_names(args.name_map); seen, created, skipped, failed = {}, [], [], []
    rows = video_rows(src); pad = max(2, len(str(len(rows))))
    aspect = parse_aspect(args.aspect); padhex = '0x%02X%02X%02X' % pad_rgb(args.pad_color)
    for r in rows:
        idx, p = r['index'], src / r['name']; digest = r['sha256']
        if digest in seen:
            skipped.append({'source_index': idx, 'source_file': r['name'], 'duplicate_of_source_index': seen[digest]['source_index'], 'duplicate_of_output_file': seen[digest]['output_file'], 'sha256': digest}); continue
        stem = names_name.get(r['name'].lower()) or names_idx.get(idx) or slugify(p.stem); output = out / f'{idx:0{pad}d}-{stem}.mp4'
        me = args.max_edge
        trc = (r.get('color_transfer') or '').lower()
        true_hdr = trc in ('arib-std-b67', 'smpte2084')
        wide_gamut = (r.get('color_primaries') or '').lower() == 'bt2020' or 'bt2020' in (r.get('color_space') or '').lower()
        convert = (not args.keep_hdr) and (true_hdr or wide_gamut)
        parts = []
        if r['fps'] > args.max_fps + .5: parts.append(f'fps={args.max_fps}')
        # Scale to even dimensions FIRST: the colorspace/zscale filters reject odd
        # sizes, so scaling must run before any color conversion.
        pad_after = None
        crop_after = None
        if aspect:
            aw, ah = aspect
            if aw >= ah: ow = me - (me % 2); oh = int(round(me * ah / aw)); oh -= oh % 2
            else: oh = me - (me % 2); ow = int(round(me * aw / ah)); ow -= ow % 2
            fit = getattr(args, 'fit', 'pad')
            if fit == 'cover':
                # Center-crop to target ratio (no letterbox). Scale up to cover, then crop.
                parts.append(f'scale={ow}:{oh}:force_original_aspect_ratio=increase:force_divisible_by=2')
                crop_after = f'crop={ow}:{oh}'
            else:
                parts.append(f'scale={ow}:{oh}:force_original_aspect_ratio=decrease:force_divisible_by=2')
                pad_after = f'pad={ow}:{oh}:(ow-iw)/2:(oh-ih)/2:color={padhex},setsar=1'
        else:
            parts.append(f"scale='if(gt(iw,ih),2*floor(min({me},iw)/2),-2)':'if(gt(iw,ih),-2,2*floor(min({me},ih)/2))'")
        if convert:
            # Normalize to Rec.709 SDR so Shopify's re-transcode does not wash out or
            # over-saturate. zscale+tonemap is the accurate HDR path (needs a real
            # HLG/PQ transfer); colorspace is the gamut-only / no-libzimg fallback and
            # tolerates an unknown transfer without crashing.
            if true_hdr and has_filter('zscale') and has_filter('tonemap'):
                parts.append('zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv')
            else:
                parts.append('colorspace=all=bt709:iall=bt2020:fast=0')
        if crop_after: parts.append(crop_after)
        if pad_after: parts.append(pad_after)
        parts.append('format=yuv420p'); vf = ','.join(parts)
        cmd = ['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(p),'-map','0:v:0','-sn','-dn','-map_metadata','-1','-vf',vf,'-c:v','libx264','-preset',args.preset,'-crf',str(args.crf),'-pix_fmt','yuv420p','-movflags','+faststart']
        if convert: cmd += ['-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv']
        cmd += ['-map','0:a?','-c:a','aac','-b:a','96k'] if args.keep_audio else ['-an']; cmd.append(str(output)); cp = run(cmd)
        if cp.returncode or not output.exists() or output.stat().st_size == 0:
            failed.append({'source_index': idx, 'source_file': r['name'], 'output_file': output.name, 'error': cp.stderr.strip()}); continue
        meta = ffprobe(output); v = stream(meta,'video'); dur = float(meta.get('format', {}).get('duration') or 0); thumb = thumbs / f'{idx:03d}.jpg'
        ss = max(.2, min(dur*.35, 3.0)) if dur else .5; run(['ffmpeg','-hide_banner','-loglevel','error','-ss',f'{ss:.2f}','-i',str(output),'-frames:v','1','-vf','scale=360:-2','-y',str(thumb)])
        item = {'source_index': idx, 'source_file': r['name'], 'output_file': output.name, 'source_bytes': r['bytes'], 'output_bytes': output.stat().st_size, 'source_mb': r['mb'], 'output_mb': round(output.stat().st_size/1048576,2), 'compression_ratio': round((1-output.stat().st_size/r['bytes'])*100,1), 'source_dimensions': f'{r["width"]}x{r["height"]}', 'output_dimensions': f'{v.get("width",0)}x{v.get("height",0)}', 'source_duration_sec': r['duration_sec'], 'output_duration_sec': round(dur,2), 'source_codec': r['video_codec'], 'output_codec': v.get('codec_name',''), 'source_color': f"{r.get('color_primaries','') or '?'}/{r.get('color_transfer','') or '?'}", 'output_color': ('bt709' if convert else 'source-preserved'), 'color_converted': ('hdr' if true_hdr and convert else ('gamut' if convert else 'no')), 'aspect': (args.aspect if aspect else 'source'), 'fit': (getattr(args, 'fit', 'pad') if aspect else 'n/a'), 'audio_removed': 'no' if args.keep_audio else 'yes', 'sha256': digest, 'thumb': str(thumb)}
        created.append(item); seen[digest] = {'source_index': idx, 'output_file': output.name}
    fields = ['source_index','source_file','output_file','source_bytes','output_bytes','source_mb','output_mb','compression_ratio','source_dimensions','output_dimensions','source_duration_sec','output_duration_sec','source_codec','output_codec','source_color','output_color','color_converted','aspect','fit','audio_removed','sha256']
    write_csv(out/'video-compression-map.csv', created, fields); write_csv(out/'skipped-duplicate-videos.csv', skipped, ['source_index','source_file','duplicate_of_source_index','duplicate_of_output_file','sha256']); write_csv(out/'failed-videos.csv', failed, ['source_index','source_file','output_file','error'])
    profile = normalize_profile(getattr(args, 'profile', 'shopify'))
    hdr_n = [i for i in created if i['color_converted'] != 'no']; overlong = [i for i in created if i['output_duration_sec'] > SHOPIFY_MAX_VIDEO_SECONDS]
    (out/'video-compression-summary.json').write_text(json.dumps({'profile': profile, 'created_count': len(created), 'skipped_exact_duplicates': len(skipped), 'failed_count': len(failed), 'hdr_converted_count': len(hdr_n), 'over_10min_count': len(overlong), 'aspect': args.aspect, 'fit': getattr(args, 'fit', 'pad'), 'created': created, 'skipped': skipped, 'failed': failed}, ensure_ascii=False, indent=2), encoding='utf-8')
    if hdr_n:
        dest = 'Shopify' if profile == 'shopify' else 'storefront SDR'
        print(f'[INFO] {len(hdr_n)} video(s) tonemapped HDR->Rec.709 SDR for {dest}: ' + ', '.join(i['output_file'] for i in hdr_n))
    if overlong and profile == 'shopify':
        print(f'[WARN] {len(overlong)} video(s) exceed Shopify 10-min limit; trim before upload: ' + ', '.join(i['output_file'] for i in overlong))
    elif overlong and profile == 'generic':
        print(f'[INFO] {len(overlong)} video(s) exceed {SHOPIFY_MAX_VIDEO_SECONDS // 60} minutes: ' + ', '.join(i['output_file'] for i in overlong))
    contact_sheet([{'path': i['thumb'], 'label': i['output_file'], 'line1': f'{i["output_dimensions"]} {i["output_duration_sec"]}s', 'line2': f'{i["source_mb"]}MB -> {i["output_mb"]}MB ({i["compression_ratio"]}%)'} for i in created], out/'compressed-video-contact-sheet.jpg', 'Compressed videos contact sheet')
    print(f'profile={profile} created={len(created)} skipped={len(skipped)} failed={len(failed)} out={out}')

def trim_video(args):
    need_ffmpeg(); out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',args.start,'-i',args.input]
    if args.duration: cmd += ['-t', args.duration]
    if args.end: cmd += ['-to', args.end]
    cmd += ['-map','0:v:0'] + (['-map','0:a?','-c:a','aac','-b:a','96k'] if args.keep_audio else ['-an']) + ['-c:v','libx264','-preset',args.preset,'-crf',str(args.crf),'-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
    cp = run(cmd)
    if cp.returncode: raise SystemExit(cp.stderr)
    print(f'wrote={out}')

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    p=sub.add_parser('inspect-images'); p.add_argument('--src', required=True); p.add_argument('--out', required=True); p.set_defaults(func=inspect_images)
    p=sub.add_parser('process-images'); p.add_argument('--src', required=True); p.add_argument('--out', required=True); p.add_argument('--name-map'); p.add_argument('--profile', choices=PROFILE_CHOICES, default='shopify', help='Target profile: shopify (default, platform QA warnings) or generic (same encode path, softer warnings).'); p.add_argument('--max-edge', type=int, default=2048); p.add_argument('--target-kb', type=int, default=950); p.add_argument('--quality', type=int, default=84); p.add_argument('--min-quality', type=int, default=74); p.add_argument('--enhance', choices=['none','auto','dark','medium','pastel','texture-safe'], default='none'); p.add_argument('--format', choices=['jpg','webp'], default='jpg'); p.add_argument('--aspect', choices=ASPECT_CHOICES, default='none'); p.add_argument('--fit', choices=['pad','cover'], default='pad'); p.add_argument('--pad-color', default='white'); p.add_argument('--focus-x', type=float, default=0.5, help='Cover-crop horizontal focal point 0..1 (0=left, 1=right, default center). Ignored for --fit pad.'); p.add_argument('--focus-y', type=float, default=0.5, help='Cover-crop vertical focal point 0..1 (0=top, 1=bottom, default center). Ignored for --fit pad.'); p.add_argument('--focus-map', help='CSV with source_file,focus_x,focus_y for per-image cover-crop focal points (overrides --focus-x/--focus-y).'); p.add_argument('--rotate-landscape', choices=['none','cw','ccw'], default='none', help='Rotate landscape images 90° to portrait (cw=clockwise, ccw=counter-clockwise). Portrait/square unchanged. 4:3 landscape becomes 3:4.'); p.add_argument('--exist-ok', action='store_true'); p.set_defaults(func=process_images)
    p=sub.add_parser('inspect-videos'); p.add_argument('--src', required=True); p.add_argument('--out', required=True); p.set_defaults(func=inspect_videos)
    p=sub.add_parser('process-videos'); p.add_argument('--src', required=True); p.add_argument('--out', required=True); p.add_argument('--name-map'); p.add_argument('--profile', choices=PROFILE_CHOICES, default='shopify', help='Target profile: shopify (default, platform QA warnings) or generic (same encode path, softer warnings).'); p.add_argument('--max-edge', type=int, default=1280); p.add_argument('--max-fps', type=int, default=30); p.add_argument('--crf', type=int, default=28); p.add_argument('--preset', default='veryfast'); p.add_argument('--keep-audio', action='store_true'); p.add_argument('--aspect', choices=ASPECT_CHOICES, default='none'); p.add_argument('--fit', choices=['pad','cover'], default='pad', help='When --aspect is set: pad=letterbox (default), cover=center-crop to ratio'); p.add_argument('--pad-color', default='white'); p.add_argument('--keep-hdr', action='store_true'); p.add_argument('--exist-ok', action='store_true'); p.set_defaults(func=process_videos)
    p=sub.add_parser('trim-video'); p.add_argument('--input', required=True); p.add_argument('--output', required=True); p.add_argument('--start', default='00:00:00'); p.add_argument('--duration'); p.add_argument('--end'); p.add_argument('--crf', type=int, default=28); p.add_argument('--preset', default='veryfast'); p.add_argument('--keep-audio', action='store_true'); p.set_defaults(func=trim_video)
    configure_console_utf8()
    args = ap.parse_args(); args.func(args)
if __name__ == '__main__': main()
