import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
import json
import re
import time
from urllib.parse import urljoin, urlparse

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

INPUT_FILE = "found_links.txt"
OUTPUT_FILE = "expanded_links.txt"
VISITED_FILE = "expander_visited.json"

MAX_DEPTH = 2             # Prevent infinite recursion
MAX_FILE_SIZE = 5_000_000 # 5 MB safety limit
TIMEOUT = 10

# Load visited
try:
    with open(VISITED_FILE, "r") as f:
        visited = json.load(f)
except FileNotFoundError:
    visited = {}

def safe_get(url):
    """Download with safety, timeouts, size limits."""
    try:
        r = requests.get(url, timeout=TIMEOUT, stream=True)

        total = 0
        content = []
        for chunk in r.iter_content(4096):
            total += len(chunk)
            if total > MAX_FILE_SIZE:
                print(f"⚠️ Skipping large file: {url}")
                return ""
            content.append(chunk)

        return b"".join(content).decode(errors="ignore")

    except:
        return ""

def normalize_url(base, link):
    """Turn relative links into absolute ones."""
    return urljoin(base, link)

def extract_from_m3u(text):
    """Extract all raw stream URLs inside M3U content."""
    return re.findall(r"(https?://[^\s\"'>]+\.m3u8?)", text)

def extract_from_xml(text):
    """Extract URLs inside XML IPTV structures."""
    links = []

    # Extract <location>http://...</location>
    loc_matches = re.findall(r"<location>(https?://.+?)</location>", text)
    links.extend(loc_matches)

    # Extract <url>http://...</url>
    url_matches = re.findall(r"<url>(https?://.+?)</url>", text)
    links.extend(url_matches)

    return links

def extract_from_html(base_url, html):
    """Extract all hyperlinks + inline m3u8 links."""
    soup = BeautifulSoup(html, "html.parser")

    links = []

    # All <a href="...">
    for a in soup.find_all("a", href=True):
        links.append(normalize_url(base_url, a["href"]))

    # Extract m3u/m3u8 inside ANY script/style/text
    links += re.findall(r"(https?://[^\s\"'>]+\.m3u8?)", html)

    return links

def determine_type(url):
    """Decide file type by extension or content-type."""
    path = urlparse(url).path.lower()
    if path.endswith(".xml"):
        return "xml"
    if path.endswith(".m3u") or path.endswith(".m3u8"):
        return "m3u"
    if path.endswith(".json"):
        return "json"
    if path.endswith(".txt"):
        return "txt"

    return "unknown"

def recursive_extract(url, depth=0):
    if depth > MAX_DEPTH:
        return []

    if url in visited:
        return []

    visited[url] = time.time()

    print(f"→ Fetching: {url}")
    text = safe_get(url)
    if not text:
        return []

    filetype = determine_type(url)
    found = set()

    # XML
    if filetype == "xml":
        found.update(extract_from_xml(text))

    # M3U
    elif filetype == "m3u":
        found.update(extract_from_m3u(text))

    # JSON (very rare, but sometimes contains lists)
    elif filetype == "json":
        try:
            data = json.loads(text)
            # extract all strings that look like URLs
            found.update(re.findall(r"https?://[^\s\"'>]+", text))
        except:
            pass

    # TXT (free lists)
    elif filetype == "txt":
        found.update(re.findall(r"https?://[^\s\"'>]+", text))

    # HTML OR UNKNOWN
    else:
        found.update(extract_from_html(url, text))

    # Recursively expand nested playlists
    final_links = set(found)

    for link in list(found):
        if link.endswith(".m3u") or link.endswith(".m3u8") or link.endswith(".xml"):
            nested = recursive_extract(link, depth + 1)
            final_links.update(nested)

    return list(final_links)

# ==============================
# MAIN PROCESS
# ==============================

try:
    with open(INPUT_FILE, "r") as f:
        start_links = list(set(line.strip() for line in f if line.strip()))
except:
    start_links = []

all_results = set()

for url in start_links:
    extracted = recursive_extract(url)
    all_results.update(extracted)

# Save visited
with open(VISITED_FILE, "w") as f:
    json.dump(visited, f, indent=2)

# Save results
with open(OUTPUT_FILE, "w") as f:
    for link in sorted(all_results):
        f.write(link + "\n")

print(f"\n=== DONE ===")
print(f"Found total {len(all_results)} stream URLs.")
print(f"Saved to {OUTPUT_FILE}")
