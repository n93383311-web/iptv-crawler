# search_engine_scraper.py
import asyncio
import aiohttp
import json
import time
import urllib.robotparser
from urllib.parse import urlparse, urlencode
from bs4 import BeautifulSoup

KEYWORDS_FILE = "keywords.txt"
QUEUE_FILE = "queue.json"

# engines: (base_url, param_name or format)
ENGINES = [
    ("https://html.duckduckgo.com/html/", "q"),   # DuckDuckGo HTML endpoint (works without JS)
    ("https://www.bing.com/search", "q"),         # Bing (HTML)
    ("https://www.mojeek.com/search", "q"),       # Mojeek
]

# concurrency throttling
MAX_CONNECTIONS = 30
REQUEST_TIMEOUT = 12
PER_ENGINE_DELAY = 1.0  # seconds between queries per engine

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

# load keywords
with open(KEYWORDS_FILE, "r", encoding="utf8") as f:
    keywords = [k.strip() for k in f if k.strip()]

# load queue
try:
    with open(QUEUE_FILE, "r", encoding="utf8") as f:
        queue = set(json.load(f))
except FileNotFoundError:
    queue = set()

# simple robots check per domain
robots_cache = {}

def can_fetch(url):
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if base in robots_cache:
        rp = robots_cache[base]
    else:
        rp = urllib.robotparser.RobotFileParser()
        try:
            rp.set_url(base + "/robots.txt")
            rp.read()
        except:
            pass
        robots_cache[base] = rp
    try:
        return rp.can_fetch(HEADERS["User-Agent"], url)
    except:
        return True

async def fetch_search(session, engine_base, param_name, query):
    params = {param_name: query}
    url = engine_base if engine_base.endswith("/") else engine_base
    # For DuckDuckGo HTML endpoint we post query as form on base URL
    if "duckduckgo" in engine_base:
        # duckduckgo expects form-encoded calldata; we'll send GET with params too
        url = engine_base
    try:
        async with session.get(engine_base, params=params, timeout=REQUEST_TIMEOUT, headers=HEADERS) as resp:
            txt = await resp.text()
            return txt
    except Exception as e:
        # timeout / connection error
        return ""

def extract_result_links(html, engine_name):
    links = set()
    soup = BeautifulSoup(html, "lxml")
    # heuristics for common engines
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Bing and DuckDuckGo often produce relative or redirect links - heuristics:
        if href.startswith("/l?") and "bing.com" in engine_name:
            continue
        if href.startswith("http") and len(href) < 300:
            links.add(href)
    return links

async def work_engine(session, engine_base, param_name):
    for kw in keywords:
        html = await fetch_search(session, engine_base, param_name, kw)
        if not html:
            await asyncio.sleep(PER_ENGINE_DELAY)
            continue
        new_links = extract_result_links(html, engine_base)
        for l in new_links:
            # quick filter: skip search engine internal links
            if any(x in l for x in ["bing.com", "duckduckgo.com", "mojeek.com", "qwant.com"]):
                continue
            # only queue HTTP/HTTPS URLs and not huge
            if l.startswith("http"):
                # respect robots for the target site
                if can_fetch(l):
                    queue.add(l)
        await asyncio.sleep(PER_ENGINE_DELAY)

async def main():
    connector = aiohttp.TCPConnector(limit=MAX_CONNECTIONS, ssl=False)  # ssl False to avoid cert issues
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for engine_base, param_name in ENGINES:
            tasks.append(work_engine(session, engine_base, param_name))
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
    # persist queue
    with open(QUEUE_FILE, "w", encoding="utf8") as f:
        json.dump(list(queue), f, indent=2, ensure_ascii=False)
    print("Search engine scraping finished. Queue size:", len(queue))
