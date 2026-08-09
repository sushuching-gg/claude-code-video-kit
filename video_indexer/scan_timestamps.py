"""
Scan Problematic Timestamps Across All 3 Videos
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("video_indexer"))
from pathlib import Path
from analyze_audio_quality import analyze_audio_track, format_time

if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

base_dir = r"H:\其他電腦\我的電腦\OneDrive\2_112淨零生活運動轉型計劃\3_資料存檔\1_115\11507內訓\課程録影"

videos = [
    ("2026-07-15碳盤查內訓 part 1.mp4", "2026-07-15 Part 1 (總長 49分55秒)"),
    ("2026-07-15碳盤查內訓1 part 2.mp4", "2026-07-15 Part 2 (總長 2小時21分06秒)"),
    ("2026-07-17碳盤查內訓 part1.mp4", "2026-07-17 Part 1 (總長 1小時58分52秒)")
]

for vname, title in videos:
    vpath = os.path.join(base_dir, vname)
    print("\n" + "="*70)
    print(f"🎬 {title}")
    print("="*70)
    res = analyze_audio_track(vpath, chunk_sec=15.0)
    print("\n【嚴重底噪 / 冷氣風扇 / 講述間隔雜訊段落】:")
    if res["noisy_segments"]:
        for idx, s in enumerate(res["noisy_segments"], 1):
            st = format_time(s["start"])
            et = format_time(s["end"])
            print(f"  {idx:02d}. ⏱️ {st} ~ {et} (噪聲: {s.get('noise_db')} dB, 信噪比 SNR: {s.get('snr')} dB)")
    else:
        print("  (無長時間持續性惡劣底噪)")

    print("\n【空間殘響 / 空曠迴音段落】:")
    if res["echo_segments"]:
        for idx, s in enumerate(res["echo_segments"][:6], 1):
            st = format_time(s["start"])
            et = format_time(s["end"])
            print(f"  {idx:02d}. ⏱️ {st} ~ {et} (迴音指數: {s.get('echo_score')})")
    else:
        print("  (無明顯迴音)")
