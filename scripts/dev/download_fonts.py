import urllib.request
import re
import os
import shutil

url = "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&display=swap"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'})

with urllib.request.urlopen(req) as response:
    css = response.read().decode('utf-8')

# Find the 400 and 700 woff2 links
# The CSS contains blocks like:
# /* latin */
# @font-face {
#   font-family: 'Space Grotesk';
#   font-style: normal;
#   font-weight: 400;
#   ...
#   src: url(https://fonts.gstatic.com/s/spacegrotesk/v15/V8mQoQDjQSkGpu8pnHXFAA_16w.woff2) format('woff2');

# We'll parse it simply
urls = re.findall(r"url\((https://[^\)]+\.woff2)\)", css)

# Google fonts can serve multiple ranges (latin, latin-ext, vietnamese). We just need the latin ones.
# In the CSS, the last one for a weight is usually latin.
# Let's extract blocks
blocks = css.split('@font-face')
latin_urls = {}
for block in blocks:
    if 'font-weight: 400' in block and '/* latin */' in block:
        m = re.search(r"url\((https://[^\)]+\.woff2)\)", block)
        if m: latin_urls['400'] = m.group(1)
    if 'font-weight: 700' in block and '/* latin */' in block:
        m = re.search(r"url\((https://[^\)]+\.woff2)\)", block)
        if m: latin_urls['700'] = m.group(1)

def download(url, path):
    print(f"Downloading {url} to {path}")
    urllib.request.urlretrieve(url, path)

os.makedirs('frontend/fonts', exist_ok=True)
os.makedirs('website/fonts', exist_ok=True)

if '400' in latin_urls:
    download(latin_urls['400'], 'frontend/fonts/space-grotesk-regular.woff2')
if '700' in latin_urls:
    download(latin_urls['700'], 'frontend/fonts/space-grotesk-bold.woff2')

# Copy to website
for w in ('regular', 'bold'):
    shutil.copy(f'frontend/fonts/space-grotesk-{w}.woff2', f'website/fonts/space-grotesk-{w}.woff2')

print("Fonts downloaded.")
