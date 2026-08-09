"""
Video Indexer & Analyzer Engine (影片分析與索引引擎)
功能：
1. 提取影片中繼資料（解析度、時長、FPS、章節）。
2. 場景偵測與關鍵影格抽樣（Keyframes / Scene Thumbnails）。
3. 離線語音轉文字辨識（ASR / Whisper），生成精確時間戳字句。
4. 輸出結構化 JSON 索引檔與視覺化搜尋播放器 UI (search_ui.html)。
"""

import os
import sys
import json
import shutil
import glob
import subprocess
from pathlib import Path

# 確保 Windows 下能找到 FFmpeg
def ensure_ffmpeg_in_path():
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    localapp = os.environ.get("LOCALAPPDATA", "")
    candidates = glob.glob(os.path.join(localapp, "Microsoft", "WinGet", "Packages", "*ffmpeg*", "**", "bin"), recursive=True)
    for c in candidates:
        if os.path.exists(os.path.join(c, "ffmpeg.exe")):
            os.environ["PATH"] = c + os.pathsep + os.environ["PATH"]
            break

ensure_ffmpeg_in_path()

if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())


def get_video_metadata(video_path: str) -> dict:
    """使用 ffprobe 提取影片詳細資訊"""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams", "-show_chapters",
        str(video_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe 讀取失敗: {res.stderr.decode('utf-8', errors='ignore')}")
    data = json.loads(res.stdout.decode('utf-8'))
    
    # 整理格式
    v_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    a_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    format_info = data.get("format", {})
    
    return {
        "filename": Path(video_path).name,
        "filepath": str(Path(video_path).resolve()),
        "duration": float(format_info.get("duration", 0)),
        "size_bytes": int(format_info.get("size", 0)),
        "bit_rate": int(format_info.get("bit_rate", 0)) if format_info.get("bit_rate") else None,
        "width": v_stream.get("width"),
        "height": v_stream.get("height"),
        "video_codec": v_stream.get("codec_name"),
        "fps": eval(v_stream.get("r_frame_rate", "0/1")) if "/" in v_stream.get("r_frame_rate", "") else 0,
        "audio_codec": a_stream.get("codec_name"),
        "chapters": data.get("chapters", [])
    }


def extract_keyframes(video_path: str, output_dir: str, interval_sec: float = 5.0) -> list:
    """提取關鍵影格縮圖與時間戳"""
    os.makedirs(output_dir, exist_ok=True)
    thumb_pattern = os.path.join(output_dir, "thumb_%04d.jpg")
    
    # 每 interval_sec 秒抓一張圖，加上場景變化偵測
    vf = f"fps=1/{interval_sec},scale=480:-1"
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", vf,
        "-q:v", "3",
        thumb_pattern
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    
    keyframes = []
    files = sorted(glob.glob(os.path.join(output_dir, "thumb_*.jpg")))
    for idx, fpath in enumerate(files):
        t = idx * interval_sec
        rel_path = os.path.relpath(fpath, Path(output_dir).parent).replace("\\", "/")
        keyframes.append({
            "timestamp": t,
            "formatted_time": format_timestamp(t),
            "image": rel_path
        })
    return keyframes


def transcribe_audio(video_path: str, model_size: str = "base", language: str = "zh") -> list:
    """使用 faster-whisper 進行語音辨識並生成時間戳"""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("[提示] faster-whisper 尚未載入，請確認已安裝。")
        return []
    
    print(f"載入 Whisper 模型 ({model_size})...")
    # CPU / GPU 自動選擇
    model = WhisperModel(model_size, device="auto", compute_type="auto")
    
    print("進行音訊辨識與時間戳提取中...")
    segments, info = model.transcribe(
        str(video_path),
        language=language,
        beam_size=5,
        word_timestamps=True
    )
    
    transcript = []
    for s in segments:
        words = []
        if s.words:
            for w in s.words:
                words.append({
                    "start": round(w.start, 2),
                    "end": round(w.end, 2),
                    "word": w.word
                })
        transcript.append({
            "id": s.id,
            "start": round(s.start, 2),
            "end": round(s.end, 2),
            "formatted_start": format_timestamp(s.start),
            "formatted_end": format_timestamp(s.end),
            "text": s.text.strip(),
            "words": words
        })
    return transcript


def format_timestamp(seconds: float) -> str:
    """轉換秒數為 00:00:00 格式"""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def generate_search_html(index_data: dict, output_path: str):
    """產出可互動的影片搜尋播放器 Web 頁面"""
    json_str = json.dumps(index_data, ensure_ascii=False, indent=2)
    video_rel = os.path.relpath(index_data["metadata"]["filepath"], Path(output_path).parent).replace("\\", "/")
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>影片內容索引與智慧搜尋 - {index_data['metadata']['filename']}</title>
<style>
  :root {{
    --bg-dark: #0f172a;
    --bg-card: #1e293b;
    --bg-hover: #334155;
    --primary: #38bdf8;
    --accent: #f43f5e;
    --neon: #34d399;
    --text-light: #f8fafc;
    --text-muted: #94a3b8;
    --border: #334155;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang TC", "Noto Sans TC", sans-serif;
    background: var(--bg-dark);
    color: var(--text-light);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  header {{
    padding: 16px 24px;
    background: #090d16;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 20px;
    font-weight: 700;
    color: var(--primary);
  }}
  .search-container {{
    position: relative;
    width: 450px;
  }}
  .search-input {{
    width: 100%;
    padding: 10px 16px 10px 42px;
    border-radius: 9999px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: #fff;
    font-size: 15px;
    outline: none;
    transition: all 0.2s;
  }}
  .search-input:focus {{
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.25);
  }}
  .search-icon {{
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    font-size: 16px;
  }}
  .main-layout {{
    flex: 1;
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 20px;
    padding: 20px;
    overflow: hidden;
  }}
  .player-section {{
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}
  .video-wrapper {{
    background: #000;
    border-radius: 12px;
    overflow: hidden;
    aspect-ratio: 16 / 9;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
  }}
  video {{
    width: 100%;
    height: 100%;
    object-fit: contain;
  }}
  .meta-card {{
    background: var(--bg-card);
    border-radius: 10px;
    padding: 16px;
    border: 1px solid var(--border);
    display: flex;
    justify-content: space-around;
    font-size: 14px;
  }}
  .meta-item {{ text-align: center; }}
  .meta-item .val {{ font-weight: 700; color: var(--primary); font-size: 16px; margin-top: 4px; }}
  .meta-item .lbl {{ color: var(--text-muted); font-size: 12px; }}

  .index-section {{
    display: flex;
    flex-direction: column;
    background: var(--bg-card);
    border-radius: 12px;
    border: 1px solid var(--border);
    overflow: hidden;
  }}
  .tabs {{
    display: flex;
    border-bottom: 1px solid var(--border);
    background: #141f32;
  }}
  .tab-btn {{
    padding: 12px 24px;
    background: none;
    border: none;
    color: var(--text-muted);
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    border-bottom: 2px solid transparent;
  }}
  .tab-btn.active {{
    color: var(--primary);
    border-bottom-color: var(--primary);
    background: var(--bg-card);
  }}
  .tab-content {{
    flex: 1;
    overflow-y: auto;
    padding: 16px;
  }}
  .transcript-item {{
    padding: 12px 14px;
    border-radius: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    cursor: pointer;
    transition: background 0.15s;
    display: flex;
    gap: 12px;
    align-items: flex-start;
  }}
  .transcript-item:hover {{
    background: var(--bg-hover);
  }}
  .time-badge {{
    background: rgba(56, 189, 248, 0.15);
    color: var(--primary);
    padding: 3px 8px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 13px;
    font-weight: bold;
    white-space: nowrap;
  }}
  .text-content {{
    flex: 1;
    font-size: 14px;
    line-height: 1.5;
  }}
  .highlight {{
    background: #f59e0b;
    color: #000;
    padding: 1px 4px;
    border-radius: 2px;
    font-weight: bold;
  }}
  .keyframe-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }}
  .keyframe-card {{
    background: #090d16;
    border-radius: 6px;
    overflow: hidden;
    cursor: pointer;
    border: 1px solid var(--border);
    transition: transform 0.15s, border-color 0.15s;
  }}
  .keyframe-card:hover {{
    transform: scale(1.03);
    border-color: var(--primary);
  }}
  .keyframe-card img {{
    width: 100%;
    height: 85px;
    object-fit: cover;
    display: block;
  }}
  .keyframe-card .time {{
    padding: 4px 6px;
    font-size: 11px;
    text-align: center;
    color: var(--text-muted);
    font-family: monospace;
  }}
</style>
</head>
<body>

<header>
  <div class="brand">
    <span>🎬</span> 影片智慧檢索與索引播放器
  </div>
  <div class="search-container">
    <span class="search-icon">🔍</span>
    <input type="text" id="searchInput" class="search-input" placeholder="搜尋影片中的語音對白、關鍵字...">
  </div>
</header>

<div class="main-layout">
  <div class="player-section">
    <div class="video-wrapper">
      <video id="videoPlayer" controls>
        <source src="{video_rel}" type="video/mp4">
        您的瀏覽器不支援 HTML5 影片播放。
      </video>
    </div>
    <div class="meta-card">
      <div class="meta-item"><div class="lbl">檔名</div><div class="val">{index_data['metadata']['filename']}</div></div>
      <div class="meta-item"><div class="lbl">片長</div><div class="val">{format_timestamp(index_data['metadata']['duration'])}</div></div>
      <div class="meta-item"><div class="lbl">解析度</div><div class="val">{index_data['metadata']['width']}x{index_data['metadata']['height']}</div></div>
      <div class="meta-item"><div class="lbl">語音段落</div><div class="val" id="segmentCount">{len(index_data['transcripts'])} 條</div></div>
    </div>
  </div>

  <div class="index-section">
    <div class="tabs">
      <button class="tab-btn active" id="tabTranscript" onclick="switchTab('transcript')">🎙️ 語音逐字索引</button>
      <button class="tab-btn" id="tabKeyframes" onclick="switchTab('keyframes')">🖼️ 關鍵影格縮圖</button>
    </div>

    <div class="tab-content" id="transcriptList"></div>
    <div class="tab-content" id="keyframeGrid" style="display:none;"></div>
  </div>
</div>

<script>
const INDEX_DATA = {json_str};
const video = document.getElementById('videoPlayer');
const searchInput = document.getElementById('searchInput');
const transcriptList = document.getElementById('transcriptList');
const keyframeGrid = document.getElementById('keyframeGrid');

function seekTo(seconds) {{
  video.currentTime = seconds;
  video.play();
}}

function renderTranscripts(query = '') {{
  transcriptList.innerHTML = '';
  const filtered = INDEX_DATA.transcripts.filter(t => 
    !query || t.text.toLowerCase().includes(query.toLowerCase())
  );
  
  if (filtered.length === 0) {{
    transcriptList.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text-muted);">查無符合的對白紀錄</div>';
    return;
  }}

  filtered.forEach(item => {{
    const div = document.createElement('div');
    div.className = 'transcript-item';
    div.onclick = () => seekTo(item.start);
    
    let text = item.text;
    if (query) {{
      const reg = new RegExp(`(${{query}})`, 'gi');
      text = text.replace(reg, '<span class="highlight">$1</span>');
    }}

    div.innerHTML = `
      <span class="time-badge">${{item.formatted_start}}</span>
      <div class="text-content">${{text}}</div>
    `;
    transcriptList.appendChild(div);
  }});
}}

function renderKeyframes() {{
  keyframeGrid.innerHTML = '';
  INDEX_DATA.keyframes.forEach(kf => {{
    const card = document.createElement('div');
    card.className = 'keyframe-card';
    card.onclick = () => seekTo(kf.timestamp);
    card.innerHTML = `
      <img src="${{kf.image}}" alt="${{kf.formatted_time}}" loading="lazy">
      <div class="time">${{kf.formatted_time}}</div>
    `;
    keyframeGrid.appendChild(card);
  }});
}}

function switchTab(tab) {{
  if (tab === 'transcript') {{
    document.getElementById('tabTranscript').classList.add('active');
    document.getElementById('tabKeyframes').classList.remove('active');
    transcriptList.style.display = 'block';
    keyframeGrid.style.display = 'none';
  }} else {{
    document.getElementById('tabTranscript').classList.remove('active');
    document.getElementById('tabKeyframes').classList.add('active');
    transcriptList.style.display = 'none';
    keyframeGrid.style.display = 'grid';
  }}
}}

searchInput.addEventListener('input', (e) => {{
  renderTranscripts(e.target.value);
}});

// 初始化渲染
renderTranscripts();
renderKeyframes();
</script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] 搜尋播放器頁面產出 -> {output_path}")


def process_video_indexing(video_file: str, output_dir: str = None, model_size: str = "base", keyframe_interval: float = 4.0):
    """主流程：分析影片、辨識對白、抽取影格、建立索引"""
    vpath = Path(video_file).resolve()
    if not vpath.exists():
        raise FileNotFoundError(f"找不到影片檔案: {vpath}")
    
    if output_dir is None:
        output_dir = vpath.parent / f"{vpath.stem}_index"
    else:
        output_dir = Path(output_dir).resolve()
        
    os.makedirs(output_dir, exist_ok=True)
    frames_dir = output_dir / "keyframes"
    
    print(f"\n==========================================")
    print(f"開始分析與建立影片索引: {vpath.name}")
    print(f"==========================================")
    
    # 1. 讀取中繼資料
    print("\n[1/4] 讀取影片格式與中繼資料...")
    metadata = get_video_metadata(str(vpath))
    
    # 2. 抽樣關鍵影格
    print(f"\n[2/4] 抽樣關鍵影格（每 {keyframe_interval} 秒一幀）...")
    keyframes = extract_keyframes(str(vpath), str(frames_dir), interval_sec=keyframe_interval)
    
    # 3. 語音辨識與時間戳
    print("\n[3/4] 進行語音轉文字與時間戳對齊...")
    transcripts = transcribe_audio(str(vpath), model_size=model_size, language="zh")
    
    # 4. 輸出結構化資料
    index_data = {
        "metadata": metadata,
        "keyframes": keyframes,
        "transcripts": transcripts
    }
    
    json_path = output_dir / "video_index.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] 結構化索引資料儲存至 -> {json_path}")
    
    # 5. 產出搜尋 UI 播放器
    ui_path = output_dir / "search_ui.html"
    generate_search_html(index_data, str(ui_path))
    
    print(f"\n==========================================")
    print(f"🎉 影片索引建立完成！")
    print(f"1. 結構化 JSON 索引：{json_path}")
    print(f"2. 視覺化搜尋播放器：{ui_path} （點擊即可在瀏覽器搜尋並跳轉）")
    print(f"==========================================\n")
    return index_data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方式: python indexer.py <影片路徑.mp4> [模型大小: tiny/base/small/medium] [抽樣秒數]")
        print("例如: python indexer.py examples/03-opus-4-8/final.mp4 base 4.0")
    else:
        video_arg = sys.argv[1]
        model_arg = sys.argv[2] if len(sys.argv) > 2 else "base"
        interval_arg = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
        process_video_indexing(video_arg, model_size=model_arg, keyframe_interval=interval_arg)
