#!/usr/bin/env python3
"""
Comprehensive branding patch:
- Replace all monopo / monopo saigon → BuildIT
- Replace Tokyo-born tagline with Dron Pancholi credit
- Add "Crafted by BuildIT in Ahmedabad, Gujarat" in tagline area
- Add "Made by Dron Pancholi" in footer data
- Patch JS bundles too
"""
import re
from pathlib import Path

SITE = Path("/home/user/app/site")

# ── 1. Patch the content database ─────────────────────────────────────────────
db_path = SITE / "_nuxt/content/db-3428b727.json"
data = db_path.read_text(encoding="utf-8")

original = data

# --- Replace remaining monopo/saigon text references ---
replacements = [
    # company name variants
    ("monopo saigon", "BuildIT"),
    ("monopo-saigon", "BuildIT"),
    ("monopo london", "BuildIT London"),
    ("monopo London", "BuildIT London"),
    ("monopo tokyo", "BuildIT Tokyo"),
    ("monopo Tokyo", "BuildIT Tokyo"),
    ("monopo New York", "BuildIT New York"),
    ("monopo new york", "BuildIT New York"),
    ("monopo nyc", "BuildIT NYC"),
    ("monopo.nyc", "BuildIT.nyc"),
    ("monopo.london", "BuildIT.london"),
    ("monopo.co.jp", "buildit.co.jp"),
    ("monopo.vn", "buildit.app"),
    ("monopo inc", "BuildIT inc"),
    ("monopo Inc", "BuildIT Inc"),
    ("@monopo", "@buildit"),
    ("monopo_", "buildit_"),
    ("monopo.", "BuildIT."),
    ("monopo,", "BuildIT,"),
    ("monopo ", "BuildIT "),
    ("monopo\"", "BuildIT\""),
    ("monopo'", "BuildIT'"),
    ("Monopo", "BuildIT"),
    ("MONOPO", "BUILDIT"),
    # social
    ("/monopo.", "/buildit."),
    ("/company/monopo", "/company/buildit"),
    ("vimeo.com/user5677798", "vimeo.com/buildit"),
    # emails
    ("contact@monopo", "contact@buildit"),
    # OG titles that may still say monopo
    ('"monopo saigon |', '"BuildIT |'),
]

for old, new in replacements:
    if old in data:
        data = data.replace(old, new)
        print(f"  replaced: {old!r} → {new!r}")

# --- Update the hero tagline / manifesto section ---
# The main tagline "We Integrate, Collaborate, and Challenge..." stays
# Add Dron Pancholi to the team section title
data = data.replace(
    'Fr<i>o</i>m T<i>o</i>ky<i>o</i> to Sa<i>i</i>gon,<br />       We c<i>o</i>me fr<i>o</i>m all<br />       <i>o</i>ver the w<i>o</i>rld',
    'Crafted w<i>i</i>th pass<i>i</i>on<br />       by Dr<i>o</i>n Panch<i>o</i>l<i>i</i>,<br />       <i>i</i>n Ahmedabad'
)
print("  Updated team section title with Dron Pancholi")

# Update the rolling/animated text on hero - "Tokyo-born" lines
data = data.replace(
    '{"is_viet":false,"first_word":"Tokyo-born,","second_word":"Creat<i>i</i>ve stud<i>i</i>o"}',
    '{"is_viet":false,"first_word":"Crafted by","second_word":"Dr<i>o</i>n Panch<i>o</i>l<i>i</i>"}'
)
print("  Updated rolling hero text with Dron Pancholi")

# Update OG meta Tokyo-born tagline
data = data.replace(
    "Tokyo-born digitally-driven creative studio",
    "Ahmedabad-born digitally-driven creative studio by Dron Pancholi"
)
print("  Updated OG tagline")

# Update the video_text_rows intro "Born in Asia, raised by the world"
data = data.replace(
    "Born in Asia, raised by the world — BuildIT is the global fulcrum between East and West. We blur boundaries of difference, creating design that stands the test of time.",
    "Born in Ahmedabad, crafted for the world — BuildIT by Dron Pancholi is the creative studio bridging ideas with execution. We blur boundaries, creating design that stands the test of time."
)
print("  Updated 'Born in Asia' intro")

# --- Add footer credit "Made by Dron Pancholi" ---
# Inject into footer's big_catchphrase area or social section
# We add a new "credit" field into the footer JSON
data = data.replace(
    '"big_catchphrase":"Keep in touch","small_catchphrase":"Start a conversation"',
    '"big_catchphrase":"Keep in touch","small_catchphrase":"Start a conversation","credit":"Made by Dron Pancholi","crafted_by":"Crafted by BuildIT in Ahmedabad, Gujarat"'
)
print("  Added footer credit fields")

# Also update VN footer
data = data.replace(
    '"big_catchphrase":"Kết nối với chúng tôi","small_catchphrase":"Trò chuyện cùng chúng tôi"',
    '"big_catchphrase":"Kết nối với chúng tôi","small_catchphrase":"Trò chuyện cùng chúng tôi","credit":"Made by Dron Pancholi","crafted_by":"Crafted by BuildIT in Ahmedabad, Gujarat"'
)
print("  Added footer credit to VN section")

# --- Write patched DB ---
db_path.write_text(data, encoding="utf-8")
print(f"\n✅ Content DB patched")

# ── 2. Patch all JS bundles ────────────────────────────────────────────────────
print("\n=== Patching JS bundles ===")

js_replacements = [
    ("monopo saigon", "BuildIT"),
    ("monopo-saigon", "BuildIT"),
    ("monopo.vn", "buildit.app"),
    ("monopo tokyo", "BuildIT Tokyo"),
    ("monopo Tokyo", "BuildIT Tokyo"),
    ("monopo london", "BuildIT London"),
    ("monopo London", "BuildIT London"),
    ("monopo_tokyo", "buildit_tokyo"),
    ("monopo_en", "buildit_en"),
    ("monopo inc", "BuildIT inc"),
    ("monopo Inc", "BuildIT Inc"),
    ("@monopo", "@buildit"),
    ("monopo.nyc", "BuildIT.nyc"),
    ("monopo.london", "BuildIT.london"),
    ("monopo.co.jp", "buildit.co.jp"),
    ("/monopo.", "/buildit."),
    ("Monopo", "BuildIT"),
    ("MONOPO", "BUILDIT"),
    # The site name in JS text
    ("monopo saigon", "BuildIT"),
    ("Tokyo-born digitally-driven creative studio", "Ahmedabad-based creative studio by Dron Pancholi"),
    ("Tokyo-born,", "Crafted by"),
]

patched_js = 0
for js_file in sorted((SITE / "_nuxt").glob("*.js")):
    original_js = js_file.read_text(encoding="utf-8", errors="replace")
    content = original_js
    for old, new in js_replacements:
        content = content.replace(old, new)
    if content != original_js:
        js_file.write_text(content, encoding="utf-8")
        print(f"  PATCHED {js_file.name}")
        patched_js += 1

print(f"\n✅ Patched {patched_js} JS files")
