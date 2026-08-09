import os
import subprocess
import sys

temp_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "cvs-render")
os.makedirs(temp_dir, exist_ok=True)
print(f"Working in: {temp_dir}")

package_json = os.path.join(temp_dir, "package.json")
if not os.path.exists(package_json):
    subprocess.run(["npm.cmd", "init", "-y"], cwd=temp_dir, check=True)

print("Installing playwright npm package...")
subprocess.run(["npm.cmd", "install", "playwright"], cwd=temp_dir, check=True)

print("Installing chromium browser...")
subprocess.run(["npx.cmd", "playwright", "install", "chromium"], cwd=temp_dir, check=True)

print("Playwright and Chromium installation complete!")
