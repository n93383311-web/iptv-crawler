import re
import json
import os

WEB_DIR = "web_results"
OUT_FILE = "keywords.txt"

def load_existing_keywords():
    if not os.path.exists(OUT_FILE):
        return set()
    with open(OUT_FILE, "r", encoding="utf8") as f:
        return set(line.strip().lower() for line in f if line.strip())

def extract_keywords_from_page(text):
    words = re.findall(r"[a-zA-Zа-яА-Я0-9]{4,}", text.lower())
    important = []
    hits = ["iptv", "m3u", "m3u8", "stream", "тв", "канал", "телевизия", "playlist"]
    for w in words:
        for h in hits:
            if h in w:
                important.append(w)
                break
    return important

def main():
    existing = load_existing_keywords()
    new_words = set()

    if not os.path.exists(WEB_DIR):
        print("No web_results directory found.")
        return

    for file in os.listdir(WEB_DIR):
        if not file.endswith(".txt"):
            continue
        with open(os.path.join(WEB_DIR, file), "r", encoding="utf8", errors="ignore") as f:
            text = f.read()
        for w in extract_keywords_from_page(text):
            if w not in existing:
                new_words.add(w)

    # Write back to keywords.txt
    with open(OUT_FILE, "a", encoding="utf8") as f:
        for w in sorted(new_words):
            f.write(w + "\n")

    print(f"Found {len(new_words)} new keywords.")

if __name__ == "__main__":
    main()
