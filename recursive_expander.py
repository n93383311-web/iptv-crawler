import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

QUEUE_FILE = "queue.json"
VISITED_FILE = "visited.json"

# Load current queue
with open(QUEUE_FILE, "r", encoding="utf-8") as f:
    queue = set(json.load(f))

# Load visited pages
with open(VISITED_FILE, "r", encoding="utf-8") as f:
    visited = set(json.load(f))

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Filter function: only allow .m3u, .m3u8, or pages with IPTV hints
def is_valid_link(url):
    if any(ext in url for ext in [".m3u", ".m3u8"]):
        return True
    if any(keyword in url.lower() for keyword in ["iptv", "tv", "live", "stream"]):
        return True
    return False

# Extract links from HTML
def extract_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        # Remove URL fragments and query strings for deduplication
        full_url = full_url.split("#")[0].split("?")[0]
        # Only keep http/https
        if full_url.startswith("http"):
            links.add(full_url)
    return links

new_links = set()

for url in list(queue):
    if url in visited:
        continue
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        page_links = extract_links(r.text, url)
        for link in page_links:
            if is_valid_link(link) and link not in visited and link not in queue:
                new_links.add(link)
    except:
        continue

# Add new links to queue
queue.update(new_links)

# Save updated queue
with open(QUEUE_FILE, "w", encoding="utf-8") as f:
    json.dump(list(queue), f, indent=2, ensure_ascii=False)

print(f"Recursive expander added {len(new_links)} new links. Total queue: {len(queue)}")
