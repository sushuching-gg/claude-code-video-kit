import os
import urllib.request

img_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "03-opus-4-8", "assets", "images")
os.makedirs(img_dir, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

images = {
    "tech.jpg": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1600&auto=format&fit=crop&q=80",
    "office.jpg": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1600&auto=format&fit=crop&q=80"
}

for name, url in images.items():
    dest = os.path.join(img_dir, name)
    print(f"Downloading {name} from {url}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response, open(dest, 'wb') as out_file:
            out_file.write(response.read())
        print(f"Successfully saved {name} to {dest}")
    except Exception as e:
        print(f"Failed to download {name}: {e}")
