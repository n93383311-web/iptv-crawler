import asyncio
import aiohttp
import aiohttp.client_exceptions
import ssl

INPUT_FILE = "found_links.txt"
OUTPUT_FILE = "bg_playlist_temp.m3u"
TIMEOUT = 10
MAX_CONNECTIONS = 100  # can increase depending on GitHub runner

# read URLs
with open(INPUT_FILE, "r") as f:
    urls = [line.strip() for line in f if line.strip()]

valid_links = []

# aiohttp connector
sslcontext = ssl.create_default_context()
conn = aiohttp.TCPConnector(limit=MAX_CONNECTIONS, ssl=sslcontext)

async def test_url(session, url):
    try:
        async with session.get(url, timeout=TIMEOUT) as response:
            if response.status == 200:
                print(f"VALID: {url}")
                valid_links.append(url)
            else:
                print(f"FAILED ({response.status}): {url}")
    except aiohttp.client_exceptions.ClientError:
        print(f"FAILED (error): {url}")
    except asyncio.TimeoutError:
        print(f"FAILED (timeout): {url}")

async def main():
    async with aiohttp.ClientSession(connector=conn) as session:
        tasks = [test_url(session, url) for url in urls]
        await asyncio.gather(*tasks)

# run
asyncio.run(main())

# write valid links to playlist
with open(OUTPUT_FILE, "w") as f:
    f.write("#EXTM3U\n")
    for url in valid_links:
        f.write(f"#EXTINF:-1,Unknown\n{url}\n")

print(f"Total valid links: {len(valid_links)}")
