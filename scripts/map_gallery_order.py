import re
import io
import json
import urllib.request
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DIR = ROOT / 'images' / 'gallery'
GALLERY_HTML = ROOT / 'gallery.html'
LIVE_ORDER_PATH = ROOT / 'scripts' / 'live_order.json'


def normalize(url_or_id: str) -> str:
    m = re.search(r'/media/([^/?]+)', url_or_id)
    if m:
        return m.group(1)
    return url_or_id.strip()


def ahash_bytes(data: bytes, size: int = 16) -> int:
    im = Image.open(io.BytesIO(data)).convert('L').resize((size, size), Image.Resampling.LANCZOS)
    pixels = list(im.getdata())
    avg = sum(pixels) / len(pixels)
    bits = 0
    for p in pixels:
        bits = (bits << 1) | (1 if p >= avg else 0)
    return bits


def ahash_file(path: Path, size: int = 16) -> int:
    with path.open('rb') as f:
        return ahash_bytes(f.read(), size=size)


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


with LIVE_ORDER_PATH.open('r', encoding='utf-8') as f:
    live_order = json.load(f)

local_files = sorted([p for p in LOCAL_DIR.glob('gallery-*') if p.is_file()])
local_hashes = {p.name: ahash_file(p) for p in local_files}

mapped_names = []
mapped_with_dist = []
remaining = set(local_hashes.keys())

for item in live_order:
    if not remaining:
        break

    media_id = normalize(item)
    ext = '.jpg'
    if media_id.lower().endswith('.png'):
        ext = '.png'
    elif media_id.lower().endswith('.jpeg'):
        ext = '.jpg'

    url = f'https://static.wixstatic.com/media/{media_id}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = resp.read()

    target_hash = ahash_bytes(data)

    best_name = None
    best_dist = 10**9
    for name in list(remaining):
        d = hamming(local_hashes[name], target_hash)
        if d < best_dist:
            best_dist = d
            best_name = name

    if best_name is None:
        break

    mapped_names.append(best_name)
    mapped_with_dist.append({"live": media_id, "local": best_name, "distance": int(best_dist)})
    remaining.discard(best_name)

# Ensure we keep all items even if live list differs in count
if remaining:
    mapped_names.extend(sorted(remaining))

with (ROOT / 'scripts' / 'mapped_order.json').open('w', encoding='utf-8') as f:
    json.dump(mapped_names, f, indent=2)

with (ROOT / 'scripts' / 'mapped_pairs.json').open('w', encoding='utf-8') as f:
    json.dump(mapped_with_dist, f, indent=2)

print(f'live_count={len(live_order)} local_count={len(local_files)} mapped={len(mapped_names)}')
print('first10=', mapped_names[:10])
