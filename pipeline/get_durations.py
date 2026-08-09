# 量測每段旁白音訊精確時長，輸出 index.html / render.py 共用的 PAGES 時長表
# 執行：python get_durations.py
import sys, os, subprocess, json, shutil, glob
from pathlib import Path

def ensure_ffmpeg_in_path():
    if shutil.which("ffprobe") and shutil.which("ffmpeg"):
        return
    localapp = os.environ.get("LOCALAPPDATA", "")
    candidates = glob.glob(os.path.join(localapp, "Microsoft", "WinGet", "Packages", "*ffmpeg*", "**", "bin"), recursive=True)
    for c in candidates:
        if os.path.exists(os.path.join(c, "ffprobe.exe")):
            os.environ["PATH"] = c + os.pathsep + os.environ["PATH"]
            break

ensure_ffmpeg_in_path()

if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

PROJECT_ROOT = Path(__file__).resolve().parent
NARRATION_DIR = PROJECT_ROOT / "assets" / "narration"

SUBTITLES = [
    "Opus 4.8 出了——但真正的突破，不是更聰明。",
    "4.7 才發 41 天，4.8 就來了。迭代快到跟不上。",
    "舊 AI 像逞強的新人；4.8 像會說「我不確定」的資深同事。",
    "更誠實、更獨立：會標不確定、不亂吹進度、抓得到重點。",
    "價格沒漲：跟 4.7 一樣 $5 進 / $25 出（每百萬 token）。",
    "Dynamic Workflow：一次派出數百個子代理，分頭做再收回。",
    "Effort 旋鈕：調低求快、調高求深。深度你說了算。",
    "Fast Mode：速度 2.5 倍、比舊版便宜 3 倍。",
    "真突破是可信度：讓 bug 溜過不出聲的機率，降到約 1/4。",
    "agentic coding 64.3% → 69.2%；首度「照搬錯誤結果」0%。",
    "日常開 Fast Mode、難題調高 Effort、大改造用 Dynamic Workflow。",
    "AI 的下一步，不是更會說，而是更敢說「不知道」。",
    "而 Mythos 級模型，數週內登場。",
]

def get_audio_duration(file_path):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(file_path)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return float(json.loads(res.stdout.decode('utf-8'))["format"]["duration"])

def main():
    PAGES_JS, total = [], 0
    for i in range(1, 14):
        p = NARRATION_DIR / f"page-{i:02d}.mp3"
        if not p.exists():
            print(f"Error: {p.name} not found!"); return
        dur = get_audio_duration(p)
        page_dur = int(round(dur + 2.2))  # tail buffer 2.2s（科普節奏較快）
        total += page_dur
        sub = SUBTITLES[i-1].replace('"', '\\"')
        PAGES_JS.append(f'  {{ i: {i}, dur: {page_dur}, sub: "{sub}" }}')
        print(f"page-{i:02d}.mp3: voice={dur:.2f}s -> page_dur={page_dur}s")
    print("\n=== const PAGES (copy to index.html) ===")
    print("const PAGES = [\n" + ",\n".join(PAGES_JS) + "\n];")
    print("\n=== PAGES_TIMINGS (copy to render.py) ===")
    print("PAGES_TIMINGS = [" + ", ".join(f'{{"i": {i+1}, "dur": {int(d.split("dur: ")[1].split(",")[0])}}}' for i, d in enumerate(PAGES_JS)) + "]")
    print(f"\nTOTAL = {total}s")

if __name__ == "__main__":
    main()
