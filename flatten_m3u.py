import requests
import re
from urllib.parse import urljoin

INPUT_FILE = "bg_playlist.m3u"
OUTPUT_FILE = "bg_playlist_final.m3u"

# Keywords to detect Bulgarian channels (optional)
BG_KEYWORDS = [
    "bnt","nova","btv","diema","bg","bul","bulgaria","канал","sofia"
]

def is_bulgarian(name, url):
    text = (name + url).lower()
    for kw in BG_KEYWORDS:
        if kw in text:
            return True
    return False

channels = []

with open(INPUT_FILE, "r") as f:
    lines = [line.strip() for line in f if line.strip()]

i = 0
while i < len(lines):
    line = lines[i]
    if line.startswith("#EXTINF"):
        # save metadata line
        meta = line
        i += 1
        url = lines[i] if i < len(lines) else None
        if url:
            channels.append((meta, url))
    elif line.startswith("http"):
        # This is likely a group playlist
        url = line
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            m3u_lines = [l.strip() for l in r.text.splitlines() if l.strip()]
            j = 0
            while j < len(m3u_lines):
                l = m3u_lines[j]
                if l.startswith("#EXTINF"):
                    meta_inner = l
                    j += 1
                    if j < len(m3u_lines):
                        url_inner = m3u_lines[j]
                        if is_bulgarian(meta_inner, url_inner):
                            channels.append((meta_inner, url_inner))
                j += 1
        except:
            print(f"Failed to fetch {url}")
    i += 1

# Remove duplicates
seen_urls = set()
final_channels = []
for meta, url in channels:
    if url not in seen_urls:
        final_channels.append((meta, url))
        seen_urls.add(url)

# Write final playlist
with open(OUTPUT_FILE, "w") as f:
    f.write("#EXTM3U\n")
    for meta, url in final_channels:
        f.write(f"{meta}\n{url}\n")

print(f"Flattened playlist created: {OUTPUT_FILE}, total channels: {len(final_channels)}")
