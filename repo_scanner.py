import json, re, requests

QUEUE_FILE = "queue.json"

with open(QUEUE_FILE, "r", encoding="utf-8") as f:
    queue = set(json.load(f))

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ------------------------
# Sources to search
# ------------------------

GITHUB_SEARCH = [
    "https://api.github.com/search/code?q=.m3u+in:file+language:text",
    "https://api.github.com/search/code?q=.m3u8+in:file+language:text"
]

GITLAB_SEARCH = [
    "https://gitlab.com/api/v4/search?scope=blobs&search=.m3u",
    "https://gitlab.com/api/v4/search?scope=blobs&search=.m3u8"
]

PASTEBIN_RAW = "https://pastebin.com/raw/{}"
PASTE_REGEX = r"pastebin\.com/([A-Za-z0-9]+)"

TELEGRAPH_REGEX = r"https://telegra\.ph/[^ \"']+"
CODEBERG_SEARCH = "https://codeberg.org/api/v1/repos/search?topic=m3u"

# -----------------------------------
# Helper: Add found URLs to queue
# -----------------------------------

def add_url(url):
    if ".m3u" in url or ".m3u8" in url:
        queue.add(url)


# -----------------------------
# GitHub scanning
# -----------------------------

def scan_github():
    for url in GITHUB_SEARCH:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            data = r.json()

            if "items" in data:
                for item in data["items"]:
                    if "html_url" in item:
                        raw = item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                        add_url(raw)

        except:
            pass


# -----------------------------
# GitLab scanning
# -----------------------------

def scan_gitlab():
    for url in GITLAB_SEARCH:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            data = r.json()

            for item in data:
                if "url" in item:
                    add_url(item["url"])

        except:
            pass


# -----------------------------
# Codeberg
# -----------------------------

def scan_codeberg():
    try:
        r = requests.get(CODEBERG_SEARCH, timeout=10, headers=HEADERS)
        data = r.json()

        for repo in data.get("data", []):
            if "html_url" in repo:
                add_url(repo["html_url"])

    except:
        pass


# -----------------------------
# Extract Pastebin URLs & convert to raw
# -----------------------------

def scan_pastebin(page_text):
    matches = re.findall(PASTE_REGEX, page_text)
    for code in matches:
        raw_url = PASTEBIN_RAW.format(code)
        add_url(raw_url)


# -----------------------------
# Telegraph scanning
# -----------------------------

def scan_telegraph(page_text):
    matches = re.findall(TELEGRAPH_REGEX, page_text)
    for link in matches:
        add_url(link)


# -----------------------------
# Run scanners
# -----------------------------

print("Scanning GitHub...")
scan_github()

print("Scanning GitLab...")
scan_gitlab()

print("Scanning Codeberg...")
scan_codeberg()

# No direct crawler here — crawler.py will fetch the page content

# --------------------------------------
# SAVE QUEUE
# --------------------------------------

with open(QUEUE_FILE, "w", encoding="utf-8") as f:
    json.dump(list(queue), f, ensure_ascii=False, indent=2)

print("Repo scanner added:", len(queue), "total URLs in queue now.")
