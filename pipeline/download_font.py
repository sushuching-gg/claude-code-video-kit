import os
import urllib.request
import zipfile
import json

font_url = "https://github.com/ButTaiwan/genseki-font/releases/download/v2.100/GenSekiGothic2TW-otf.zip"
fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
os.makedirs(fonts_dir, exist_ok=True)
zip_path = os.path.join(fonts_dir, "GenSekiGothic2TW-otf.zip")

print(f"Downloading GenSekiGothic font from {font_url}...")
try:
    urllib.request.urlretrieve(font_url, zip_path)
    print("Download finished, extracting...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(fonts_dir)
    print("Fonts extracted to:", fonts_dir)
    if os.path.exists(zip_path):
        os.remove(zip_path)
except Exception as e:
    print(f"Font download error: {e}")
