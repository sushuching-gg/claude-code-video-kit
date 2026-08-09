"""
自動切出環境底噪片段與合輯音檔
"""

import os
import subprocess
import shutil
import glob
from pathlib import Path

# 確保 Windows 下能找到 FFmpeg
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

video_file = r"video_indexer/2026-07-17碳盤查內訓 part1.mp4"
out_dir = Path("video_indexer/2026-07-17碳盤查內訓 part1_index/noise_samples")
out_dir.mkdir(parents=True, exist_ok=True)

# 6 個主要環境底噪區段 (start, end, desc)
segments = [
    ("00:00:00", "00:02:45", "01_開場設備與環境底噪"),
    ("00:18:30", "00:21:15", "02_冷氣風扇低頻嗡鳴"),
    ("00:35:00", "00:37:30", "03_講述間隔高底噪"),
    ("00:58:15", "01:02:00", "04_現場環境音干擾"),
    ("01:15:30", "01:21:00", "05_翻頁操作空檔雜訊"),
    ("01:42:15", "01:45:00", "06_討論間隔背景雜音")
]

print("開始切出環境底噪試聽音檔...")
clip_files = []
for idx, (st, et, label) in enumerate(segments, 1):
    clip_name = f"{label}.mp3"
    clip_path = out_dir / clip_name
    cmd = [
        "ffmpeg", "-y", "-ss", st, "-to", et, "-i", video_file,
        "-vn", "-c:a", "libmp3lame", "-b:a", "192k", str(clip_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    clip_files.append(clip_path)
    print(f"[OK] 已產出: {clip_name} ({st} ~ {et})")

# 合成一個連續播放的合輯音檔
concat_list = out_dir / "concat_list.txt"
with open(concat_list, "w", encoding="utf-8") as f:
    for c in clip_files:
        f.write(f"file '{c.name}'\n")

combo_mp3 = out_dir / "00_全部環境底噪連續試聽合輯.mp3"
cmd_concat = [
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
    "-c", "copy", str(combo_mp3)
]
subprocess.run(cmd_concat, cwd=str(out_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
if concat_list.exists():
    os.remove(concat_list)

print(f"\n🎉 完成！已產出合輯：{combo_mp3}")
