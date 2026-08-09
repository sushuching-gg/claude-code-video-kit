"""
Professional Audio Denoising & Noise Removal Engine (專業音訊降噪與環境音消除)
針對 06_討論間隔背景雜音.mp3 進行多種等級的降噪演算法處理與對比產出。
"""

import os
import subprocess
import shutil
import glob
from pathlib import Path

def ensure_ffmpeg_in_path():
    if shutil.which("ffmpeg"):
        return
    localapp = os.environ.get("LOCALAPPDATA", "")
    candidates = glob.glob(os.path.join(localapp, "Microsoft", "WinGet", "Packages", "*ffmpeg*", "**", "bin"), recursive=True)
    for c in candidates:
        if os.path.exists(os.path.join(c, "ffmpeg.exe")):
            os.environ["PATH"] = c + os.pathsep + os.environ["PATH"]
            break

ensure_ffmpeg_in_path()

input_mp3 = Path("video_indexer/2026-07-17碳盤查內訓 part1_index/noise_samples/06_討論間隔背景雜音.mp3")
out_dir = Path("video_indexer/2026-07-17碳盤查內訓 part1_index/denoised_samples")
out_dir.mkdir(parents=True, exist_ok=True)

# 方案 1：FFT 動態頻譜降噪 (平滑自然版 - 消除冷氣/風扇/室內恆定噪聲，不傷人聲)
# afftdn: nr (noise reduction dB), nf (noise floor dB), tn (track noise)
v1_file = out_dir / "06_降噪方案1_FFT頻譜降噪_自然平衡版.mp3"
cmd_v1 = [
    "ffmpeg", "-y", "-i", str(input_mp3),
    "-af", "afftdn=nr=18:nf=-38:tn=1,highpass=f=75",
    "-c:a", "libmp3lame", "-b:a", "192k", str(v1_file)
]

# 方案 2：極致靜音降噪 (FFT降噪 + 智慧語音門限 agate - 講話停頓時背景完全純淨無聲)
v2_file = out_dir / "06_降噪方案2_極致靜音門限_停頓無雜音版.mp3"
cmd_v2 = [
    "ffmpeg", "-y", "-i", str(input_mp3),
    "-af", "highpass=f=80,afftdn=nr=22:nf=-35:tn=1,agate=threshold=0.018:ratio=9:attack=20:release=250",
    "-c:a", "libmp3lame", "-b:a", "192k", str(v2_file)
]

# 方案 3：廣播級人聲強化 (低頻切除 + 動態壓縮 + 人聲頻段增益 EQ + 降噪)
v3_file = out_dir / "06_降噪方案3_廣播級清晰人聲強化版.mp3"
cmd_v3 = [
    "ffmpeg", "-y", "-i", str(input_mp3),
    "-af", "highpass=f=85,lowpass=f=11000,afftdn=nr=16:nf=-40:tn=1,equalizer=f=3000:t=q:w=1.5:g=3.5,acompressor=threshold=-21dB:ratio=3:attack=15:release=180",
    "-c:a", "libmp3lame", "-b:a", "192k", str(v3_file)
]

print("=== 開始執行音訊降噪演算法 ===")
for name, cmd, out_f in [
    ("方案 1: FFT 自然頻譜降噪", cmd_v1, v1_file),
    ("方案 2: 極致靜音門限降噪", cmd_v2, v2_file),
    ("方案 3: 廣播級人聲強化降噪", cmd_v3, v3_file)
]:
    print(f"正在運算 {name}...")
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print(f"[OK] 產出 -> {out_f.name}")

print("\n降噪處理完成！")
