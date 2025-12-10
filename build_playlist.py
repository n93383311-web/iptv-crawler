#!/usr/bin/env python3
# build_playlist.py
# Reads bg_playlist_temp.m3u (tested working URLs)
# Filters for Bulgarian channels using bg_channel_keywords.txt
# Outputs bg_playlist.m3u (clean, deduplicated) and bg_playlist_unfiltered.m3u (all tested links)

import re
import os

TEMP_FILE = "bg_playlist_temp.m3u"
OUTPUT_FILE = "bg_playlist.m3u"
UNFILTERED = "bg_playlist_unfiltered.m3u"
KW_FILE = "bg_channel_keywords.txt"

# Load Bulgarian keywords (lowercased)
bg_keywords = []
if os.path.exists(KW_FILE):
    with open(KW_FILE, "r", encoding="utf8") as f:
        for line in f:
            w = line.strip()
            if w:
                bg_keywords.append(w.lower())

def looks_bulgarian(meta, url):
    """
    Decide whether this channel is Bulgarian.
    - meta: the EXTINF text (may be empty)
    - url: the stream URL
    """
    text = (meta or "") + " " + (url or "")
    text = text.lower()
    # quick exact / substring match against keywords
    for kw in bg_keywords:
        # use word boundary or substring where appropriate
        if kw in text:
            return True
    # heuristic: if the URL domain ends with .bg -> likely Bulgarian
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        if host.endswith(".bg"):
            return True
    except:
        pass
    return False

def parse_m3u_lines(lines):
    """
    Parse lines from a temp m3u which may contain #EXTINF lines and URLs
    Return list of tuples: (meta, url)
    """
    out = []
    meta = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            meta = line
            continue
        if line.startswith("#"):
            continue
        # a URL line
        url = line
        out.append((meta, url))
        meta = ""
    return out

# Read temp file
if not os.path.exists(TEMP_FILE):
    print(f"{TEMP_FILE} not found. Nothing to do.")
    exit(0)

with open(TEMP_FILE, "r", encoding="utf8", errors="ignore") as f:
    lines = [l.rstrip("\n") for l in f]

entries = parse_m3u_lines(lines)

# Save unfiltered list (for manual inspection)
with open(UNFILTERED, "w", encoding="utf8") as f:
    f.write("#EXTM3U\n")
    for meta, url in entries:
        if meta:
            f.write(meta + "\n")
        f.write(url + "\n")

# Filter Bulgarian channels
final = []
seen = set()
for meta, url in entries:
    url = url.strip()
    meta_text = meta.strip() if meta else ""
    if url in seen:
        continue
    if looks_bulgarian(meta_text, url):
        # Derive name
        name = None
        # Try to extract human name from EXTINF
        m = re.search(r'#EXTINF:[^\n,]*,(.+)$', meta_text)
        if m:
            name = m.group(1).strip()
        if not name:
            # Derive from host
            try:
                from urllib.parse import urlparse
                host = urlparse(url).hostname or url
                name = host
            except:
                name = url
        # Ensure name is simple
        name = re.sub(r'[\r\n]+', '', name)
        final.append((name, url))
        seen.add(url)

# Write final playlist
with open(OUTPUT_FILE, "w", encoding="utf8") as f:
    f.write("#EXTM3U\n")
    for name, url in final:
        f.write(f"#EXTINF:-1,{name}\n{url}\n")

print(f"Wrote {len(final)} Bulgarian channels to {OUTPUT_FILE}")
print(f"Unfiltered tested links saved to {UNFILTERED}")
