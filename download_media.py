#!/usr/bin/env python3
"""Download all media assets referenced in the content database"""
import re, time, urllib.parse
from pathlib import Path
import requests

BASE_URL = "https://monopo.vn"
OUT = Path("/home/user/app/site")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://monopo.vn/",
})

# read all sources for asset refs
sources = [
    OUT / "_nuxt/content/db-3428b727.json",
    *list((OUT / "_nuxt").glob("*.js")),
]

paths = set()
for src in sources:
    try:
        content = src.read_text(errors="ignore")
        found = re.findall(r'"(/[^"]+\.(?:png|jpg|jpeg|gif|webp|svg|mp4|webm|woff2?|ttf|eot|otf|pdf))"', content)
        paths.update(found)
        # also grab paths without extension that might be images (strapi media)
        found2 = re.findall(r'"(/media/[^"?#]+)"', content)
        paths.update(found2)
    except:
        pass

print(f"Total asset paths found: {len(paths)}")

ok = 0
fail = 0
skip = 0

for path in sorted(paths):
    url = BASE_URL + path
    out_path = OUT / path.lstrip("/")

    if out_path.exists():
        skip += 1
        continue

    try:
        r = session.get(url, timeout=30, stream=True)
        if r.status_code == 404:
            fail += 1
            continue
        r.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        size = out_path.stat().st_size
        print(f"  OK [{size:>9,}] {path}")
        ok += 1
        time.sleep(0.03)
    except Exception as e:
        print(f"  FAIL {path} -> {e}")
        fail += 1

print(f"\n✅ Downloaded: {ok}, Skipped: {skip}, Failed: {fail}")
