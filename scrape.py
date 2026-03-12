#!/usr/bin/env python3
"""
Full website scraper for monopo.vn
Downloads HTML, CSS, JS, images, fonts and all linked assets
"""
import os
import re
import sys
import time
import hashlib
import urllib.parse
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://monopo.vn"
OUTPUT_DIR = Path("/home/user/app/site")
OUTPUT_DIR.mkdir(exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
})

downloaded = set()
failed = set()

def url_to_path(url):
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lstrip('/')
    if parsed.query:
        path += '?' + parsed.query
    # sanitize
    path = re.sub(r'[<>:"|?*]', '_', path)
    if not path or path.endswith('/'):
        path = path + 'index.html'
    elif '.' not in Path(path).name:
        path = path + '/index.html'
    return OUTPUT_DIR / path

def download(url, referer=None):
    if url in downloaded or url in failed:
        return None
    if not url.startswith('http'):
        return None
    # only download from monopo.vn and CDN domains
    parsed = urllib.parse.urlparse(url)
    allowed = ['monopo.vn', 'fonts.googleapis.com', 'fonts.gstatic.com']
    if not any(d in parsed.netloc for d in allowed):
        print(f"  [SKIP] {url}")
        return None

    out_path = url_to_path(url)
    downloaded.add(url)

    if out_path.exists():
        print(f"  [CACHED] {url}")
        return out_path

    try:
        headers = {}
        if referer:
            headers['Referer'] = referer
        print(f"  [GET] {url}")
        r = session.get(url, timeout=30, headers=headers, allow_redirects=True)
        r.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(r.content)
        time.sleep(0.1)
        return out_path
    except Exception as e:
        print(f"  [FAIL] {url} -> {e}")
        failed.add(url)
        return None

def resolve(url, base):
    if not url or url.startswith('data:') or url.startswith('blob:') or url.startswith('#'):
        return None
    if url.startswith('//'):
        url = 'https:' + url
    elif url.startswith('/'):
        url = BASE_URL + url
    elif not url.startswith('http'):
        url = urllib.parse.urljoin(base, url)
    return url

def extract_urls_from_css(css_text, css_url):
    urls = []
    for m in re.finditer(r'url\(["\']?([^"\')\s]+)["\']?\)', css_text):
        u = resolve(m.group(1), css_url)
        if u:
            urls.append(u)
    for m in re.finditer(r'@import\s+["\']([^"\']+)["\']', css_text):
        u = resolve(m.group(1), css_url)
        if u:
            urls.append(u)
    return urls

def extract_urls_from_js(js_text, js_url):
    urls = []
    # look for /_nuxt/ and similar path references
    for m in re.finditer(r'["\'](\/_nuxt\/[^"\']+)["\']', js_text):
        u = resolve(m.group(1), BASE_URL)
        if u:
            urls.append(u)
    for m in re.finditer(r'["\']([^"\']*\.(?:png|jpg|jpeg|gif|webp|svg|mp4|webm|woff2?|ttf|eot|otf)[^"\']*)["\']', js_text):
        raw = m.group(1)
        if raw.startswith('/') or raw.startswith('http'):
            u = resolve(raw, BASE_URL)
            if u:
                urls.append(u)
    return urls

def scrape_page(page_url):
    print(f"\n[PAGE] {page_url}")
    try:
        r = session.get(page_url, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"  [FAIL] {page_url} -> {e}")
        return None, []

    html = r.text
    out_path = url_to_path(page_url)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding='utf-8')
    downloaded.add(page_url)

    soup = BeautifulSoup(html, 'lxml')
    asset_urls = []
    page_urls = []

    # scripts
    for tag in soup.find_all('script', src=True):
        u = resolve(tag['src'], page_url)
        if u:
            asset_urls.append(u)
    # inline scripts — extract asset refs
    for tag in soup.find_all('script'):
        if tag.string:
            asset_urls.extend(extract_urls_from_js(tag.string, page_url))

    # stylesheets
    for tag in soup.find_all('link', rel=lambda x: x and 'stylesheet' in x):
        u = resolve(tag.get('href', ''), page_url)
        if u:
            asset_urls.append(u)

    # preload links
    for tag in soup.find_all('link', rel=lambda x: x and ('preload' in x or 'prefetch' in x)):
        u = resolve(tag.get('href', ''), page_url)
        if u:
            asset_urls.append(u)

    # images
    for tag in soup.find_all(['img', 'source']):
        for attr in ['src', 'srcset', 'data-src']:
            val = tag.get(attr, '')
            if val:
                for part in val.split(','):
                    u = resolve(part.strip().split()[0], page_url)
                    if u:
                        asset_urls.append(u)

    # og images, meta
    for tag in soup.find_all('meta'):
        val = tag.get('content', '')
        if val and (val.startswith('/') or val.startswith('http')):
            u = resolve(val, page_url)
            if u and any(val.endswith(ext) for ext in ['.png','.jpg','.jpeg','.gif','.webp','.svg']):
                asset_urls.append(u)

    # internal page links
    for tag in soup.find_all('a', href=True):
        href = tag['href']
        if href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
            continue
        u = resolve(href, page_url)
        if u and 'monopo.vn' in u:
            page_urls.append(u)

    return html, asset_urls, page_urls

def process_asset(url):
    path = download(url, referer=BASE_URL)
    if path and path.exists():
        content_type = ''
        name = path.name.lower()
        if name.endswith('.css'):
            try:
                css = path.read_text(encoding='utf-8', errors='ignore')
                sub_urls = extract_urls_from_css(css, url)
                for u in sub_urls:
                    download(u, referer=url)
            except:
                pass
        elif name.endswith('.js'):
            try:
                js = path.read_text(encoding='utf-8', errors='ignore')
                sub_urls = extract_urls_from_js(js, url)
                for u in sub_urls:
                    download(u, referer=url)
            except:
                pass

# ── MAIN ──────────────────────────────────────────────────────────────────────
pages_to_visit = [BASE_URL + '/']
visited_pages = set()

# known sub-pages from monopo.vn
extra_pages = [
    BASE_URL + '/work',
    BASE_URL + '/about',
    BASE_URL + '/services',
    BASE_URL + '/contact',
    BASE_URL + '/blog',
    BASE_URL + '/careers',
]
pages_to_visit.extend(extra_pages)

while pages_to_visit:
    page_url = pages_to_visit.pop(0)
    # normalise
    page_url = page_url.split('#')[0].rstrip('/')
    if not page_url:
        page_url = BASE_URL
    if page_url in visited_pages:
        continue
    visited_pages.add(page_url)

    result = scrape_page(page_url)
    if result is None:
        continue
    html, assets, sub_pages = result

    for a in assets:
        process_asset(a)

    for p in sub_pages:
        p = p.split('#')[0].rstrip('/')
        if p not in visited_pages and p not in pages_to_visit:
            pages_to_visit.append(p)

print(f"\n✅ Done! Downloaded {len(downloaded)} files. Failed: {len(failed)}")
print("Failed URLs:")
for f in list(failed)[:20]:
    print(f"  {f}")
