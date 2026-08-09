"""
Extract A/B Comparison Audio Clips (抽取問題音軌之修復前／修復後對比試聽片段)
"""

import os
import sys
import subprocess
from pathlib import Path

if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

base_orig_dir = r"H:\其他電腦\我的電腦\OneDrive\2_112淨零生活運動轉型計劃\3_資料存檔\1_115\11507內訓\課程録影"
base_enh_dir = r"video_indexer/batch_enhanced"
out_dir = Path("video_indexer/ab_comparison_samples")
out_dir.mkdir(parents=True, exist_ok=True)

# 定義要拉出來對比的代表性問題片段清單 (影片代號, 原始檔名, 修復檔名, 起始時間, 結束時間, 標籤名稱, 特徵說明)
comparison_segments = [
    # --- 2026-07-17 Part 1 ---
    {
        "video": "2026-07-17 Part 1",
        "orig_file": os.path.join(base_orig_dir, "2026-07-17碳盤查內訓 part1.mp4"),
        "enh_file": os.path.join(base_enh_dir, "2026-07-17碳盤查內訓 part1_已修復高清音質.mp4"),
        "start": "01:42:15",
        "end": "01:44:30",
        "name": "01_0717Part1_旁人笑聲與討論嬉鬧段落",
        "desc": "原始錄音在中間出現明顯旁人笑聲與「找不到啊/哪一個」等碎嘴，修復後主講清晰、笑聲柔化為遠方微弱底色。"
    },
    {
        "video": "2026-07-17 Part 1",
        "orig_file": os.path.join(base_orig_dir, "2026-07-17碳盤查內訓 part1.mp4"),
        "enh_file": os.path.join(base_enh_dir, "2026-07-17碳盤查內訓 part1_已修復高清音質.mp4"),
        "start": "00:00:00",
        "end": "00:01:30",
        "name": "02_0717Part1_開場設備與冷氣低頻底噪",
        "desc": "開場未發言時的冷氣低頻風扇聲與設備電流底噪，修復後底噪被大幅消除且維持自然空間感。"
    },
    {
        "video": "2026-07-17 Part 1",
        "orig_file": os.path.join(base_orig_dir, "2026-07-17碳盤查內訓 part1.mp4"),
        "enh_file": os.path.join(base_enh_dir, "2026-07-17碳盤查內訓 part1_已修復高清音質.mp4"),
        "start": "00:18:30",
        "end": "00:20:00",
        "name": "03_0717Part1_風扇嗡鳴與講述停頓雜訊",
        "desc": "講述間隔中的風扇運轉嗡鳴與空調聲，修復後人聲更厚實溫暖、停頓處背景平滑安靜。"
    },

    # --- 2026-07-15 Part 1 ---
    {
        "video": "2026-07-15 Part 1",
        "orig_file": os.path.join(base_orig_dir, "2026-07-15碳盤查內訓 part 1.mp4"),
        "enh_file": os.path.join(base_enh_dir, "2026-07-15碳盤查內訓 part 1_已修復高清音質.mp4"),
        "start": "00:00:00",
        "end": "00:01:30",
        "name": "04_0715Part1_開場環境音與麥克風空檔",
        "desc": "開場設備調試、走動與室內空氣噪音，修復後主講聲音明亮且背景雜訊被有效平抑。"
    },
    {
        "video": "2026-07-15 Part 1",
        "orig_file": os.path.join(base_orig_dir, "2026-07-15碳盤查內訓 part 1.mp4"),
        "enh_file": os.path.join(base_enh_dir, "2026-07-15碳盤查內訓 part 1_已修復高清音質.mp4"),
        "start": "00:24:30",
        "end": "00:26:00",
        "name": "05_0715Part1_講述空檔與空調持續噪聲",
        "desc": "中段說話停頓時的空調持續噪聲，修復後人聲溫潤飽滿，無抽氣斷點感。"
    },

    # --- 2026-07-15 Part 2 ---
    {
        "video": "2026-07-15 Part 2",
        "orig_file": os.path.join(base_orig_dir, "2026-07-15碳盤查內訓1 part 2.mp4"),
        "enh_file": os.path.join(base_enh_dir, "2026-07-15碳盤查內訓1 part 2_已修復高清音質.mp4"),
        "start": "00:00:00",
        "end": "00:01:30",
        "name": "06_0715Part2_中場重啟麥克風雜訊與底噪",
        "desc": "下半場剛開始時的現場嘈雜聲與設備噪聲，修復後背景明顯純淨。"
    },
    {
        "video": "2026-07-15 Part 2",
        "orig_file": os.path.join(base_orig_dir, "2026-07-15碳盤查內訓1 part 2.mp4"),
        "enh_file": os.path.join(base_enh_dir, "2026-07-15碳盤查內訓1 part 2_已修復高清音質.mp4"),
        "start": "01:10:00",
        "end": "01:11:30",
        "name": "07_0715Part2_課堂學員互動與講述間隔",
        "desc": "講授間隔現場碎語與冷氣聲，修復後主講咬字清晰通透。"
    }
]

print("=== 開始抽取問題音軌之【修復前】vs【修復後】試聽對比音檔 ===")

results = []
for item in comparison_segments:
    st = item["start"]
    et = item["end"]
    tag = item["name"]
    
    orig_mp3 = out_dir / f"{tag}__原始未處理.mp3"
    enh_mp3 = out_dir / f"{tag}__修復後方案3C.mp3"
    
    print(f"\n正在抽取: {tag} ({st} ~ {et})...")
    
    # 抽取原始音檔
    cmd_orig = [
        "ffmpeg", "-y", "-ss", st, "-to", et, "-i", item["orig_file"],
        "-vn", "-c:a", "libmp3lame", "-b:a", "192k", str(orig_mp3)
    ]
    subprocess.run(cmd_orig, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"  [OK] 產出原始未處理: {orig_mp3.name}")
    
    # 抽取修復後音檔
    cmd_enh = [
        "ffmpeg", "-y", "-ss", st, "-to", et, "-i", item["enh_file"],
        "-vn", "-c:a", "libmp3lame", "-b:a", "192k", str(enh_mp3)
    ]
    subprocess.run(cmd_enh, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"  [OK] 產出修復後音檔: {enh_mp3.name}")
    
    results.append({
        "video": item["video"],
        "tag": tag,
        "time": f"{st} ~ {et}",
        "desc": item["desc"],
        "orig_file": orig_mp3,
        "enh_file": enh_mp3
    })

print("\n" + "="*70)
print(f"🎉 全部 {len(results)} 組對比試聽音檔抽取完成！")
print(f"📁 儲存目錄: {out_dir.resolve()}")
print("="*70)
