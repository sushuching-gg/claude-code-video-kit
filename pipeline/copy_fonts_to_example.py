import os
import shutil

src_dir = os.path.join(os.path.dirname(__file__), "fonts")
dst_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "03-opus-4-8", "assets", "fonts")
os.makedirs(dst_dir, exist_ok=True)

for fname in os.listdir(src_dir):
    if fname.endswith(".otf"):
        shutil.copy2(os.path.join(src_dir, fname), os.path.join(dst_dir, fname))
        print(f"Copied font {fname} to {dst_dir}")
