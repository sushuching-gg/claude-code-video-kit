"""
Fast Acoustic Timestamp Scanner for all 3 videos
"""

import os
import sys
import subprocess
from pathlib import Path
import soundfile as sf
import numpy as np

if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

base_dir = r"H:\其他電腦\我的電腦\OneDrive\2_112淨零生活運動轉型計劃\3_資料存檔\1_115\11507內訓\課程録影"

videos = [
    ("2026-07-15碳盤查內訓 part 1.mp4", "2026-07-15 Part 1", 2995.0),
    ("2026-07-15碳盤查內訓1 part 2.mp4", "2026-07-15 Part 2", 8466.7),
    ("2026-07-17碳盤查內訓 part1.mp4", "2026-07-17 Part 1", 7132.4)
]

def format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

print("=== 快速掃描三部影片之問題音訊時間戳 ===")

for vname, label, dur in videos:
    vpath = os.path.join(base_dir, vname)
    print("\n" + "="*70)
    print(f"🎬 【{label}】(總長度: {format_time(dur)})")
    print("="*70)
    
    # 抽取 8kHz 單聲道 raw float PCM
    cmd = ["ffmpeg", "-y", "-i", vpath, "-ac", "1", "-ar", "8000", "-f", "f32le", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    raw, _ = p.communicate()
    
    audio = np.frombuffer(raw, dtype=np.float32)
    sr = 8000
    
    # 5 秒步長
    win_sec = 5.0
    win_samples = int(win_sec * sr)
    num_wins = len(audio) // win_samples
    
    noisy_moments = []
    laughter_or_chatter = []
    
    for w in range(num_wins):
        sec = w * win_sec
        chunk = audio[w * win_samples : (w + 1) * win_samples]
        rms = np.sqrt(np.mean(chunk**2) + 1e-12)
        rms_db = 20 * np.log10(rms + 1e-12)
        peak = np.max(np.abs(chunk))
        
        # 20ms frames to get noise floor
        sub = np.abs(chunk[:(len(chunk)//160)*160].reshape(-1, 160))
        sub_energies = np.sqrt(np.mean(sub**2, axis=1) + 1e-12)
        n_floor_db = 20 * np.log10(np.percentile(sub_energies, 15) + 1e-12)
        
        # 1. 持續性冷氣底噪/風扇噪音 (Noise floor > -32dB)
        if n_floor_db > -31.5 and rms_db > -26.0:
            noisy_moments.append((sec, sec + win_sec, round(float(n_floor_db), 1), round(float(rms_db), 1)))
            
        # 2. 講者停頓時的旁人突發笑聲/碎嘴 (Noise floor 低但有中等突發能量 Peak 0.4~0.8)
        if -38.0 < rms_db < -22.0 and peak > 0.45 and (peak / (rms + 1e-6)) > 4.5:
            laughter_or_chatter.append((sec, sec + win_sec, round(float(peak), 2)))
            
    # 合併連續區間
    def merge(items, gap=15.0):
        if not items:
            return []
        merged = []
        cur_st, cur_et = items[0][0], items[0][1]
        for it in items[1:]:
            if it[0] - cur_et <= gap:
                cur_et = it[1]
            else:
                merged.append((cur_st, cur_et))
                cur_st, cur_et = it[0], it[1]
        merged.append((cur_st, cur_et))
        return merged
        
    m_noisy = merge(noisy_moments)
    m_chatter = merge(laughter_or_chatter)
    
    print("📌 推薦抽檢之【重點雜音／笑聲／空調嗡鳴】時間點：")
    combined = sorted(list(set(m_noisy + m_chatter)), key=lambda x: x[0])
    if combined:
        for idx, (st, et) in enumerate(combined[:8], 1):
            print(f"  {idx:02d}. ⏱️ {format_time(st)} ~ {format_time(et)} (分秒: {int(st//60):02d}分{int(st%60):02d}秒 ~ {int(et//60):02d}分{int(et%60):02d}秒)")
    else:
        print("  • 開場前 00:00:00 ~ 00:01:30 (開場底噪)")
        print(f"  • 中段說話停頓處")
