import json, re, requests
from bs4 import BeautifulSoup

SEARCH_ENGINES = [
    "https://html.duckduckgo.com/html/?q=",
    "https://www.mojeek.com/search?q=",
    "https://lite.qwant.com/?q="
]

KEYWORDS_FILE = "keywords.json"
QUEUE_FILE = "queue.json"

with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
    keywords = json.load(f)

with open(QUEUE_FILE, "r", encoding="utf-8") as f:
    queue = set(json.load(f))

def extract_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        url = a["href"]
        if url.startswith("http") and len(url) < 200:
            links.append(url)
    return links

for keyword in keywords:
    for engine in SEARCH_ENGINES:
        try:
            print(f"Searching: {engine}{keyword}")
            r = requests.get(engine + keyword, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            links = extract_links(r.text)

            for link in links:
                if ".m3u" in link or ".m3u8" in link or "tv" in link or "stream" in link:
                    queue.add(link)
        except:
            pass

# save
with open(QUEUE_FILE, "w", encoding="utf-8") as f:
    json.dump(list(queue), f, indent=2, ensure_ascii=False)

print("Search crawler added:", len(queue), "links")
