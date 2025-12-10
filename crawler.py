import requests
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin, urlparse

# === LOAD EXTRA KEYWORDS ===
EXTRA_KEYWORDS = []
try:
    with open("keywords.txt", "r", encoding="utf8") as f:
        EXTRA_KEYWORDS = [x.strip() for x in f if x.strip()]
except FileNotFoundError:
    EXTRA_KEYWORDS = []

MAX_PAGES_PER_RUN = 50
SEEDS_FILE = "seeds.txt"
QUEUE_FILE = "queue.json"
VISITED_FILE = "visited.json"
FOUND_FILE = "found_links.txt"

# Load visited pages
try:
    with open(VISITED_FILE, "r") as f:
        visited = json.load(f)
except FileNotFoundError:
    visited = {}

# Load queue
try:
    with open(QUEUE_FILE, "r") as f:
        queue = json.load(f)
except FileNotFoundError:
    queue = []

# If queue is empty, start with seeds
if not queue:
    with open(SEEDS_FILE, "r") as f:
        queue = [line.strip() for line in f if line.strip()]

found_links = []

def is_html(url):
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        content_type = r.headers.get("Content-Type","").lower()
        return "text/html" in content_type
    except:
        return False

def extract_links(url):
    links = []
    m3u_links = []
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        # All anchor hrefs
        for a in soup.find_all("a", href=True):
            link = urljoin(url, a['href'])
            links.append(link)
        # Raw .m3u/.m3u8 links in text
        m3u_links += re.findall(r'(https?://[^\s\'"<>]+\.m3u8?)', html)
    except:
        return [], []
    return links, m3u_links

pages_crawled = 0
while queue and pages_crawled < MAX_PAGES_PER_RUN:
    current_url = queue.pop(0)
    if current_url in visited:
        continue
    if not current_url.startswith("http"):
        continue
    if not is_html(current_url):
        visited[current_url] = time.time()
        continue
    new_links, new_m3u = extract_links(current_url)
    # add new links to queue
    for link in new_links:
        if link not in visited and link not in queue:
            queue.append(link)
    # add found m3u links
    found_links.extend(new_m3u)
    # mark visited
    visited[current_url] = time.time()
    pages_crawled += 1
    time.sleep(1)  # polite delay

# Save visited
with open(VISITED_FILE, "w") as f:
    json.dump(visited, f, indent=2)

# Save queue
with open(QUEUE_FILE, "w") as f:
    json.dump(queue, f, indent=2)

# Save found links
with open(FOUND_FILE, "a") as f:
    for link in found_links:
        f.write(link+"\n")

print(f"Crawled {pages_crawled} pages, found {len(found_links)} potential links.")

