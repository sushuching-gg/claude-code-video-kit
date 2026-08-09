import json
import os
import sys

if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

index_path = "video_indexer/2026-07-17碳盤查內訓 part1_index/video_index.json"
with open(index_path, "r", encoding="utf-8") as f:
    data = json.load(f)

meta = data.get("metadata", {})
transcripts = data.get("transcripts", [])
keyframes = data.get("keyframes", [])

print("=== 影片基本資訊 ===")
print(f"檔案: {meta.get('filename')}")
print(f"時長: {meta.get('duration')} 秒 ({int(meta.get('duration')//60)} 分 {int(meta.get('duration')%60)} 秒)")
print(f"解析度: {meta.get('width')}x{meta.get('height')} @ {meta.get('fps')} fps")
print(f"總語音段落數: {len(transcripts)} 條")
print(f"總關鍵影格縮圖: {len(keyframes)} 張\n")

print("=== 10 分鐘區間時間軸重點摘要 ===")
interval_sec = 600
for mark in range(0, int(meta.get('duration', 0)), interval_sec):
    m_start = mark
    m_end = mark + 60
    m, s = divmod(mark, 60)
    h, m = divmod(m, 60)
    time_str = f"{h:02d}:{m:02d}:{s:02d}"
    
    seg_texts = [t['text'] for t in transcripts if mark <= t['start'] < mark + 45]
    summary = " ".join(seg_texts[:3]) if seg_texts else "(段落轉換/靜音/簡報展示)"
    print(f"⏱️ [{time_str}] {summary[:60]}...")
