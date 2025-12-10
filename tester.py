import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

INPUT_FILE = "found_links.txt"
OUTPUT_FILE = "bg_playlist_temp.m3u"
MAX_THREADS = 20  # adjust depending on system/network speed
TIMEOUT = 10      # seconds

# read URLs
with open(INPUT_FILE, "r") as f:
    urls = [line.strip() for line in f if line.strip()]

valid_links = []

def test_url(url):
    try:
        r = requests.get(url, timeout=TIMEOUT, stream=True)
        if r.status_code == 200:
            return url
    except:
        pass
    return None

# parallel testing
with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    future_to_url = {executor.submit(test_url, url): url for url in urls}
    for future in as_completed(future_to_url):
        url = future_to_url[future]
        result = future.result()
        if result:
            valid_links.append(result)
            print(f"VALID: {result}")
        else:
            print(f"FAILED: {url}")

# write valid links to playlist
with open(OUTPUT_FILE, "w") as f:
    f.write("#EXTM3U\n")
    for url in valid_links:
        f.write(f"#EXTINF:-1,Unknown\n{url}\n")

print(f"Total valid links: {len(valid_links)}")
