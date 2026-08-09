import os
import subprocess
import winreg

bin_dir = r"C:\Users\asus\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin"

# 1. Update current environment PATH
if bin_dir not in os.environ["PATH"]:
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]

# 2. Update Windows User PATH in registry
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
        user_path, _ = winreg.QueryValueEx(key, "Path")
        if bin_dir.lower() not in user_path.lower():
            new_path = bin_dir + ";" + user_path
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            print("Successfully added FFmpeg to HKCU\\Environment\\Path")
        else:
            print("FFmpeg already present in HKCU\\Environment\\Path")
except Exception as e:
    print(f"Registry update warning: {e}")

# 3. Test execution
res1 = subprocess.run([os.path.join(bin_dir, "ffmpeg.exe"), "-version"], capture_output=True, text=True)
print("FFmpeg version output:", res1.stdout.splitlines()[0] if res1.stdout else "Failed")

res2 = subprocess.run([os.path.join(bin_dir, "ffprobe.exe"), "-version"], capture_output=True, text=True)
print("FFprobe version output:", res2.stdout.splitlines()[0] if res2.stdout else "Failed")
