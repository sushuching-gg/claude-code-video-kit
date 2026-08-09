"""
CLI Video Search Tool (影片內容命令列搜尋器)
使用方式：
python search.py <video_index.json 路徑> <搜尋關鍵字>
"""

import sys
import json
from pathlib import Path

if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def search_index(json_file: str, query: str):
    p = Path(json_file)
    if not p.exists():
        print(f"錯誤: 找不到索引檔案 {json_file}")
        return
    
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    meta = data.get("metadata", {})
    transcripts = data.get("transcripts", [])
    
    print(f"\n==========================================")
    print(f"🔍 搜尋影片: {meta.get('filename')} (片長: {meta.get('duration')}s)")
    print(f"關鍵字: 「{query}」")
    print(f"==========================================")
    
    matches = [t for t in transcripts if query.lower() in t.get("text", "").lower()]
    
    if not matches:
        print("未找到包含該關鍵字的對白段落。")
        return
    
    print(f"找到 {len(matches)} 筆相符片段：\n")
    for i, m in enumerate(matches, 1):
        highlighted = m['text'].replace(query, f"\033[1;33m{query}\033[0m")
        print(f"[{i}] ⏱️ 時間: {m['formatted_start']} - {m['formatted_end']} ({m['start']}s ~ {m['end']}s)")
        print(f"    對白: {highlighted}")
        print()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方式: python search.py <video_index.json> <關鍵字>")
        print("例如: python search.py ./output_index/video_index.json 突破")
    else:
        search_index(sys.argv[1], sys.argv[2])
