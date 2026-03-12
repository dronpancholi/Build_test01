#!/usr/bin/env python3
"""
Complete scraper for monopo.vn - downloads all JS chunks, CSS, images, fonts
"""
import os, re, time, urllib.parse
from pathlib import Path
import requests

BASE_URL = "https://monopo.vn"
OUT = Path("/home/user/app/site")
OUT.mkdir(exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://monopo.vn/",
})

ok = set()
fail = set()

# All JS chunks extracted from 9a94800.js loader
JS_CHUNKS = [
    "9a94800", "8d8fa77", "be4e259", "aa1acf2",
    "5865639", "f51300c", "689c731", "f5cfbd3", "9cadd6c",
    "085ef8d", "be6af92", "0abff57", "2369e4a", "2fa46b3",
    "1b8e902", "493896a", "2c6ef22", "cf6ad66", "275c444",
    "8d9611b", "5f8a04a", "5cede2d", "68b4a6b", "519c627",
    "b31f3d9", "69e1fc1", "32f59d8", "5cd67dd"
]

def download(url, out_path):
    if url in ok or url in fail:
        return
    ok.add(url)
    if out_path.exists():
        print(f"  CACHED {url}")
        return
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(r.content)
        print(f"  OK  [{len(r.content):>8}] {url}")
        time.sleep(0.05)
    except Exception as e:
        fail.add(url)
        ok.discard(url)
        print(f"  FAIL {url} -> {e}")

# ── 1. Download homepage HTML ────────────────────────────────────────────────
print("\n=== Downloading homepage ===")
r = session.get(BASE_URL + "/", timeout=30)
html = r.text
(OUT / "index.html").write_text(html, encoding="utf-8")
print(f"  OK  homepage ({len(html)} bytes)")

# ── 2. Download all JS chunks ────────────────────────────────────────────────
print("\n=== Downloading JS chunks ===")
nuxt_dir = OUT / "_nuxt"
nuxt_dir.mkdir(exist_ok=True)
for chunk in JS_CHUNKS:
    url = f"{BASE_URL}/_nuxt/{chunk}.js"
    download(url, nuxt_dir / f"{chunk}.js")

# ── 3. Parse JS for more asset refs ─────────────────────────────────────────
print("\n=== Scanning JS bundles for assets ===")
all_asset_refs = set()
for js_file in nuxt_dir.glob("*.js"):
    content = js_file.read_text(errors="ignore")
    # image/font/svg refs
    for m in re.finditer(r'"(/[^"]+\.(png|jpg|jpeg|gif|webp|svg|mp4|webm|woff2?|ttf|eot|otf))"', content):
        all_asset_refs.add(m.group(1))
    for m in re.finditer(r"'(/[^']+\.(png|jpg|jpeg|gif|webp|svg|mp4|webm|woff2?|ttf|eot|otf))'", content):
        all_asset_refs.add(m.group(1))
    # /_nuxt/ refs
    for m in re.finditer(r'"(/_nuxt/[^"]+)"', content):
        all_asset_refs.add(m.group(1))
    for m in re.finditer(r"'(/_nuxt/[^']+)'", content):
        all_asset_refs.add(m.group(1))

print(f"  Found {len(all_asset_refs)} asset refs in JS")

# ── 4. Download all referenced assets ───────────────────────────────────────
print("\n=== Downloading assets ===")
for ref in sorted(all_asset_refs):
    url = BASE_URL + ref
    # compute local path
    path = ref.lstrip("/")
    out_path = OUT / path
    download(url, out_path)

# ── 5. Download root-level assets from HTML ──────────────────────────────────
print("\n=== Downloading root assets ===")
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, "lxml")

root_assets = []
for tag in soup.find_all(["link", "script", "img"]):
    for attr in ["href", "src"]:
        val = tag.get(attr, "")
        if val and not val.startswith("http") and not val.startswith("//") and val.startswith("/"):
            root_assets.append(val)

for tag in soup.find_all("meta"):
    val = tag.get("content", "")
    if val and val.startswith("/") and any(val.endswith(x) for x in [".png",".jpg",".svg",".ico",".webmanifest"]):
        root_assets.append(val)

for ref in set(root_assets):
    url = BASE_URL + ref
    path = ref.lstrip("/")
    if not path:
        continue
    out_path = OUT / path
    download(url, out_path)

# ── 6. Download polyfill scripts ─────────────────────────────────────────────
print("\n=== Downloading polyfills ===")
polyfills = [
    "https://cdnjs.cloudflare.com/ajax/libs/babel-polyfill/7.6.0/polyfill.min.js",
    "https://polyfill.io/v3/polyfill.min.js?features=fetch%2CObject.entries%2CObject.assign%2CCustomEvent%2CElement.prototype.append%2CNodeList.prototype.forEach%2CIntersectionObserver%2Csmoothscroll",
]
poly_dir = OUT / "polyfills"
poly_dir.mkdir(exist_ok=True)
for url in polyfills:
    fname = "babel-polyfill.min.js" if "babel" in url else "polyfill-io.js"
    download(url, poly_dir / fname)

# ── 7. Deep scan — download any new JS chunks found in downloaded chunks ─────
print("\n=== Deep scanning for more JS chunks ===")
extra_chunks = set()
for js_file in nuxt_dir.glob("*.js"):
    content = js_file.read_text(errors="ignore")
    # Look for chunk hash references like "5865639" that are not yet downloaded
    for m in re.finditer(r'"([0-9a-f]{7})"', content):
        h = m.group(1)
        if h not in JS_CHUNKS:
            extra_chunks.add(h)

print(f"  Potential extra chunks: {len(extra_chunks)}")
for h in sorted(extra_chunks):
    url = f"{BASE_URL}/_nuxt/{h}.js"
    try:
        r = session.head(url, timeout=10)
        if r.status_code == 200:
            download(url, nuxt_dir / f"{h}.js")
    except:
        pass

# ── 8. Download Nuxt content JSON (API) ──────────────────────────────────────
print("\n=== Downloading Nuxt content API ===")
content_urls = [
    "/_content/home",
    "/_content/work",
    "/_content/about",
    "/_content/services",
    "/_content/contact",
    "/_content/blog",
]
api_dir = OUT / "_content"
api_dir.mkdir(exist_ok=True)
for path in content_urls:
    url = BASE_URL + path
    try:
        r2 = session.get(url, timeout=15, headers={"Accept": "application/json"})
        if r2.status_code == 200:
            fname = path.strip("/").replace("/","_") + ".json"
            (api_dir / fname).write_bytes(r2.content)
            print(f"  OK  {url}")
    except Exception as e:
        print(f"  FAIL {url} -> {e}")

# ── Report ───────────────────────────────────────────────────────────────────
all_files = list(OUT.rglob("*"))
files = [f for f in all_files if f.is_file()]
print(f"\n✅ Done! {len(files)} files in site/")
print(f"   Failed: {len(fail)}")
for f in list(fail)[:10]:
    print(f"   {f}")
