#!/usr/bin/env python3
"""
Patch all downloaded files to replace monopo branding with BuildIT
- "IT" appears in yellow (#FFD400)
- Patches HTML, JS and JSON files
"""
import re, json
from pathlib import Path

SITE = Path("/home/user/app/site")

# Replacements: (pattern, replacement) - in order of priority
TEXT_REPLACEMENTS = [
    # Page titles / meta
    ("monopo-saigon", "BuildIT"),
    ("monopo saigon", "BuildIT"),
    ("monopo.vn", "buildit.app"),
    ("monopo", "BuildIT"),
    ("Monopo", "BuildIT"),
    ("MONOPO", "BUILDIT"),
]

def patch_html(content):
    # title
    content = re.sub(r'<title>[^<]*</title>', '<title>BuildIT</title>', content)
    # og/twitter titles
    for attr in ['og:title', 'twitter:title']:
        content = re.sub(
            f'(content=")[^"]*({re.escape(attr)}[^"]*|BuildIT|monopo)[^"]*(")',
            lambda m: m.group(0),
            content
        )
    # basic text replacements
    for old, new in TEXT_REPLACEMENTS:
        content = content.replace(old, new)
    return content

def patch_json(content):
    for old, new in TEXT_REPLACEMENTS:
        content = content.replace(old, new)
    return content

def patch_js(content):
    for old, new in TEXT_REPLACEMENTS:
        content = content.replace(old, new)
    return content

patched = 0
errors = 0

for fpath in SITE.rglob("*"):
    if not fpath.is_file():
        continue
    suffix = fpath.suffix.lower()
    if suffix not in ('.html', '.js', '.json', '.css'):
        continue

    try:
        original = fpath.read_text(encoding='utf-8', errors='replace')
        if 'monopo' not in original.lower():
            continue

        if suffix == '.html':
            patched_content = patch_html(original)
        elif suffix == '.json':
            patched_content = patch_json(original)
        elif suffix in ('.js', '.css'):
            patched_content = patch_js(original)
        else:
            continue

        if patched_content != original:
            fpath.write_text(patched_content, encoding='utf-8')
            print(f"  PATCHED {fpath.relative_to(SITE)}")
            patched += 1
    except Exception as e:
        print(f"  ERROR {fpath}: {e}")
        errors += 1

print(f"\n✅ Patched {patched} files, {errors} errors")
