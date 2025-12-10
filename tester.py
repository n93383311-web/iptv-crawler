import requests
import time

FOUND_FILE = "found_links.txt"
TEMP_FILE = "bg_playlist_temp.m3u"

TIMEOUT = 5

def test_url(url):
    try:
        r = requests.get(url, timeout=TIMEOUT, stream=True)
        if r.status_code == 200:
            content_type = r.headers.get("Content-Type","").lower()
            if "mpegurl" in content_type or "audio/mpegurl" in content_type:
                return True
    except:
        return False
    return False

tested = set()
try:
    with open(TEMP_FILE, "r") as f:
        tested = set([line.strip() for line in f if line.strip() and not line.startswith("#")])
except:
    pass

valid_links = []

with open(FOUND_FILE, "r") as f:
    for line in f:
        url = line.strip()
        if url in tested:
            continue
        if test_url(url):
            valid_links.append(url)
            print("Valid:", url)
        time.sleep(1)

with open(TEMP_FILE, "a") as f:
    for url in valid_links:
        f.write(url+"\n")

print(f"Tested links, {len(valid_links)} new valid streams found.")

