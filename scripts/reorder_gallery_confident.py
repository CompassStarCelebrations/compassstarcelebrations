import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "gallery.html"
PAIRS = ROOT / "scripts" / "mapped_pairs.json"
THRESHOLD = 10

text = GALLERY.read_text(encoding="utf-8")

img_pat = re.compile(r'<div class="gallery-item"><img src="images/gallery/(gallery-\d+\.(?:jpg|png))" alt=""></div>')
images = img_pat.findall(text)
if not images:
    raise RuntimeError("Could not find gallery image list")

cap_block_pat = re.compile(r'(const captions = \[\n)(.*?)(\n\s*\];)', re.S)
cap_match = cap_block_pat.search(text)
if not cap_match:
    raise RuntimeError("Could not find captions array")

cap_entries = re.findall(r'^\s*\{ title: .*? \},?\s*$', cap_match.group(2), re.M)
if len(cap_entries) != len(images):
    raise RuntimeError(f"Images ({len(images)}) and captions ({len(cap_entries)}) counts differ")

pairs = json.loads(PAIRS.read_text(encoding="utf-8"))

high_conf = []
for p in pairs:
    if int(p.get("distance", 9999)) <= THRESHOLD:
        name = p["local"]
        if name in images and name not in high_conf:
            high_conf.append(name)

remaining = [n for n in images if n not in high_conf]
new_order = high_conf + remaining

if len(new_order) != len(images):
    raise RuntimeError("Reorder size mismatch")

index_by_name = {name: i for i, name in enumerate(images)}
perm = [index_by_name[n] for n in new_order]
new_caps = [cap_entries[i] for i in perm]

new_img_lines = "\n".join([f'            <div class="gallery-item"><img src="images/gallery/{name}" alt=""></div>' for name in new_order])
text = img_pat.sub(lambda m: "", text)

# Replace full image block between gallery-grid div open and closing for consistency
grid_pat = re.compile(r'(<div class="gallery-grid">\n)(.*?)(\n\s*</div>)', re.S)
grid_match = grid_pat.search(text)
if not grid_match:
    raise RuntimeError("Could not find gallery-grid block")
text = text[:grid_match.start(2)] + new_img_lines + text[grid_match.end(2):]

new_cap_block = cap_match.group(1) + "\n".join(new_caps) + cap_match.group(3)
text = text[:cap_match.start()] + new_cap_block + text[cap_match.end():]

GALLERY.write_text(text, encoding="utf-8")

print(f"images={len(images)} high_conf={len(high_conf)}")
print("first12 order:", new_order[:12])
