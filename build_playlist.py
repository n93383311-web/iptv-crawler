import re

TEMP_FILE = "bg_playlist_temp.m3u"
OUTPUT_FILE = "bg_playlist.m3u"

BG_KEYWORDS = [
    "bg","bul","bulgaria","bnt","nova","btv","diema","sofia",
    "bnt1","bnt2","bnt3","канал","европа","thevoice"
]

def is_bulgarian(url, name=""):
    text = url.lower() + " " + name.lower()
    for kw in BG_KEYWORDS:
        if kw in text:
            return True
    return False

existing = set()
try:
    with open(OUTPUT_FILE, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                existing.add(line.strip())
except:
    pass

with open(TEMP_FILE, "r") as f:
    lines = [line.strip() for line in f if line.strip()]

with open(OUTPUT_FILE, "a") as f:
    if f.tell() == 0:
        f.write("#EXTM3U\n")
    for url in lines:
        if url in existing:
            continue
        if is_bulgarian(url):
            # Use host as name fallback
            host = re.findall(r"https?://([^/]+)/?", url)
            name = host[0] if host else url
            f.write(f"#EXTINF:-1,{name}\n{url}\n")
            existing.add(url)

print(f"Playlist updated, total channels: {len(existing)}")

