# dedupe_keywords.py
import os

INFILE = "keywords.txt"
TMP = "keywords_clean.txt"

if not os.path.exists(INFILE):
    print("No keywords.txt found.")
    exit(0)

seen = set()
out = []
with open(INFILE, "r", encoding="utf8") as f:
    for line in f:
        w = line.strip().lower()
        if not w: 
            continue
        if w not in seen:
            seen.add(w)
            out.append(w)

with open(TMP, "w", encoding="utf8") as f:
    for w in sorted(out):
        f.write(w + "\n")

# replace file
os.replace(TMP, INFILE)
print(f"Dedupe done, {len(out)} unique keywords.")
