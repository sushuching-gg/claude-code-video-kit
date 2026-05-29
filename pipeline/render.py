# 渲染引擎：Python + Playwright + FFmpeg（科普 Opus 4.8）
# 執行：python render.py
import os, sys, shutil, subprocess, glob
from pathlib import Path

if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

PROJECT_ROOT = Path(__file__).resolve().parent
RENDERS_DIR = PROJECT_ROOT / "renders"
RENDERS_DIR.mkdir(parents=True, exist_ok=True)
NARRATION_DIR = PROJECT_ROOT / "assets" / "narration"
RECORD_CJS = PROJECT_ROOT / "record.cjs"

# 與 index.html 的 PAGES 完全對齊
PAGES_TIMINGS = [
    {"i": 1, "dur": 11}, {"i": 2, "dur": 14}, {"i": 3, "dur": 17}, {"i": 4, "dur": 16},
    {"i": 5, "dur": 13}, {"i": 6, "dur": 17}, {"i": 7, "dur": 15}, {"i": 8, "dur": 13},
    {"i": 9, "dur": 15}, {"i": 10, "dur": 15}, {"i": 11, "dur": 12}, {"i": 12, "dur": 13},
    {"i": 13, "dur": 10},
]

def get_node_env():
    env = os.environ.copy()
    temp_dir = env.get("TEMP", "C:\\Temp")
    env["NODE_PATH"] = os.path.join(temp_dir, "cvs-render", "node_modules")
    return env

def compile_master_audio():
    print("\n--- [1/3] 合成主音軌 ---")
    master = RENDERS_DIR / "master_audio.mp3"
    if master.exists(): os.remove(master)
    padded = []
    for page in PAGES_TIMINGS:
        idx, dur = page["i"], page["dur"]
        src = NARRATION_DIR / f"page-{idx:02d}.mp3"
        dst = RENDERS_DIR / f"padded-page-{idx:02d}.mp3"
        if not src.exists(): raise FileNotFoundError(f"找不到 {src}")
        if dst.exists(): os.remove(dst)
        cmd = ["ffmpeg", "-y", "-i", str(src), "-af", "apad", "-t", str(dur), str(dst)]
        print(f"  填充 page-{idx:02d} -> {dur}s")
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode != 0:
            print(r.stderr.decode('utf-8', errors='ignore')); r.check_returncode()
        padded.append(dst)
    concat = RENDERS_DIR / "concat_list.txt"
    with open(concat, "w", encoding="utf-8") as f:
        for p in padded: f.write(f"file '{p.name}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(master)]
    r = subprocess.run(cmd, cwd=str(RENDERS_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        print(r.stderr.decode('utf-8', errors='ignore')); r.check_returncode()
    for p in padded:
        try: os.remove(p)
        except: pass
    try: os.remove(concat)
    except: pass
    print(f"[OK] 主音軌 -> {master}")

def record_video():
    print("\n--- [2/3] Playwright 錄影 ---")
    env = get_node_env()
    for f in glob.glob(str(RENDERS_DIR / "*.webm")):
        try: os.remove(f)
        except: pass
    subprocess.run(["node", str(RECORD_CJS)], cwd=str(PROJECT_ROOT), env=env, check=True, shell=True)
    webms = glob.glob(str(RENDERS_DIR / "*.webm"))
    if not webms: raise FileNotFoundError("Playwright 沒產出 webm！")
    target = RENDERS_DIR / "video.webm"
    if target.exists(): os.remove(target)
    shutil.move(webms[0], target)
    print(f"[OK] 無聲影像 -> {target}")

def mux_final_video():
    print("\n--- [3/3] mux 影像 + 音軌 ---")
    video = RENDERS_DIR / "video.webm"
    master = RENDERS_DIR / "master_audio.mp3"
    final = PROJECT_ROOT / "final.mp4"
    if final.exists(): os.remove(final)
    cmd = ["ffmpeg", "-y", "-i", str(video), "-i", str(master),
           "-map", "0:v", "-map", "1:a",  # 強制丟棄 webm 無聲軌（GOTCHAS E-2）
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        print(r.stderr.decode('utf-8', errors='ignore')); r.check_returncode()
    print(f"[OK] 最終影片 -> {final}")

def main():
    print("=== OPUS 4.8 科普影片渲染管線 ===")
    try:
        compile_master_audio()
        record_video()
        mux_final_video()
        print(f"\n=== 完成！輸出：{PROJECT_ROOT / 'final.mp4'} ===")
    except Exception as e:
        print(f"\n[ERROR] {e}"); sys.exit(1)

if __name__ == "__main__":
    main()
