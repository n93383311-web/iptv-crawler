import requests
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin, urlparse

MAX_PAGES_PER_RUN = 50
SEEDS_FILE = "seeds.txt"
QUEUE_FILE = "queue.json"
VISITED_FILE = "visited.json"
FOUND_FILE = "found_links.txt"
KEYWORDS_FILE = "keywords.txt"

# -----------------------------
# LOAD VISITED PAGES
# -----------------------------
try:
    with open(VISITED_FILE, "r") as f:
        visited = json.load(f)
except FileNotFoundError:
    visited = {}

# -----------------------------
# LOAD QUEUE
# -----------------------------
try:
    with open(QUEUE_FILE, "r") as f:
        queue = json.load(f)
except FileNotFoundError:
    queue = []

# -----------------------------
# LOAD KEYWORDS FOR AUTO-EXPANDING SEARCH
# -----------------------------
EXTRA_KEYWORDS = []
try:
    with open(KEYWORDS_FILE, "r", encoding="utf8") as f:
        EXTRA_KEYWORDS = [x.strip() for x in f if x.strip()]
except FileNotFoundError:
    EXTRA_KEYWORDS = []

# -----------------------------
# IF QUEUE IS EMPTY → LOAD SEEDS
# -----------------------------
if not queue:
    with open(SEEDS_FILE, "r") as f:
        queue = [line.strip() for line in f if line.strip()]

# -----------------------------
# EXTEND QUEUE WITH SEARCH QUERIES (NEW)
# -----------------------------
search_queries = [
    "bg iptv playlist",
    "bulgaria m3u",
    "бг m3u8",
    "българска телевизия онлайн"
]

# Add dynamic keywords to search queries
for kw in EXTRA_KEYWORDS:
    search_queries.append(f"{kw} iptv")
    search_queries.append(f"{kw} m3u")
    search_queries.append(f"{kw} m3u8")
    search_queries.append(f"{kw} bg tv")
    search_queries.append(f"{kw} бг тв")
    search_queries.append(f"{kw} бг телевизия")

# Convert all queries → Google search URLs
for query in search_queries:
    google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    if google_url not in queue and google_url not in visited:
        queue.append(google_url)

found_links = []

# -----------------------------
# CHECK IF URL IS HTML
# -----------------------------
def is_html(url):
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        content_type = r.headers.get("Content-Type","").lower()
        return "text/html" in content_type
    except:
        return False

# -----------------------------
# EXTRACT LINKS FROM PAGE
# -----------------------------
def extract_links(url):
    links = []
    m3u_links = []
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        # Anchor hrefs
        for a in soup.find_all("a", href=True):
            link = urljoin(url, a['href'])
            links.append(link)
        # Raw .m3u / .m3u8 URLs in text
        m3u_links += re.findall(r'(https?://[^\s\'"<>]+\.m3u8?)', html)
    except:
        return [], []
    return links, m3u_links

# -----------------------------
# MAIN CRAWLING LOOP
# -----------------------------
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

    # Add new normal links into queue
    for link in new_links:
        if link not in visited and link not in queue:
            queue.append(link)

    # Add found m3u links
    found_links.extend(new_m3u)

    # Mark visited
    visited[current_url] = time.time()
    pages_crawled += 1
    time.sleep(1)

# -----------------------------
# SAVE UPDATED DATA
# -----------------------------
with open(VISITED_FILE, "w") as f:
    json.dump(visited, f, indent=2)

with open(QUEUE_FILE, "w") as f:
    json.dump(queue, f, indent=2)

with open(FOUND_FILE, "a") as f:
    for link in found_links:
        f.write(link + "\n")

print(f"Crawled {pages_crawled} pages, found {len(found_links)} potential links.")
