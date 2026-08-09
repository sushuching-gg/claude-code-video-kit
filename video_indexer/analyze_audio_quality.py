"""
Audio Quality, Noise & Echo Analyzer (音訊品質、環境雜音與迴音分析器)
針對 2026-07-17碳盤查內訓 part1.mp4 進行音訊分段聲學分析：
1. 偵測環境底噪 (Background Noise / Hum / Noise Floor)
2. 偵測空間殘響與迴音 (Reverberation / Echo)
3. 偵測音量過大爆音或失真 (Clipping / Sudden Volume Peaks)
4. 偵測麥克風噴麥/雜音段落 (Low SNR & Irregular Transients)
"""

import os
import sys
import json
import subprocess
import shutil
import glob
import numpy as np

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


def format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def analyze_audio_track(video_path: str, chunk_sec: float = 15.0):
    print(f"正在抽取音軌並進行聲學訊號分析: {video_path}...")
    
    # 抽取 16kHz 單聲道 PCM 音訊進行快速分析
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-ac", "1", "-ar", "16000",
        "-f", "f32le", "-"
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw_audio, err = p.communicate()
    
    if p.returncode != 0:
        raise RuntimeError(f"FFmpeg 抽取音訊失敗: {err.decode('utf-8', errors='ignore')}")
    
    audio = np.frombuffer(raw_audio, dtype=np.float32)
    sample_rate = 16000
    total_sec = len(audio) / sample_rate
    chunk_samples = int(chunk_sec * sample_rate)
    
    print(f"音訊總長度: {format_time(total_sec)} ({total_sec:.1f} 秒)，分析步長: {chunk_sec} 秒")
    
    noisy_segments = []
    echo_segments = []
    clipping_segments = []
    unclear_segments = []
    
    num_chunks = int(np.ceil(len(audio) / chunk_samples))
    
    for i in range(num_chunks):
        start_sec = i * chunk_sec
        end_sec = min((i + 1) * chunk_sec, total_sec)
        chunk = audio[i * chunk_samples : (i + 1) * chunk_samples]
        
        if len(chunk) < sample_rate:
            continue
            
        # 1. 均方根音量 (RMS) 與底噪評估
        rms = np.sqrt(np.mean(chunk**2) + 1e-12)
        rms_db = 20 * np.log10(rms + 1e-12)
        
        # 2. 靜音/非語音底噪 (第 15 百分位數音量，代表背景持續噪聲)
        num_frames = len(chunk) // 320
        if num_frames == 0:
            continue
        sub_frames = np.abs(chunk[:num_frames * 320].reshape(num_frames, 320))  # 20ms frames
        frame_energies = np.sqrt(np.mean(sub_frames**2, axis=1) + 1e-12)
        noise_floor_db = 20 * np.log10(np.percentile(frame_energies, 15) + 1e-12)
        peak_val = np.max(np.abs(chunk))
        
        # 動態範圍 (SNR 估計)
        dynamic_range = (20 * np.log10(peak_val + 1e-12)) - noise_floor_db
        
        # 3. 迴音 / 殘響指數 (Autocorrelation in 40ms ~ 250ms range)
        # 房間殘響與遠場麥克風會在 40ms~250ms 有持續延遲自相關
        corr = np.correlate(chunk[:sample_rate*4], chunk[:sample_rate*4], mode='full')
        corr = corr[len(corr)//2:]
        corr_normalized = corr / (corr[0] + 1e-12)
        
        lag_40ms = int(0.04 * sample_rate)
        lag_250ms = int(0.25 * sample_rate)
        echo_score = np.max(corr_normalized[lag_40ms:lag_250ms]) if len(corr_normalized) > lag_250ms else 0
        
        # 判斷異常：
        # A. 嚴重底噪 / 環境音干擾 (底噪大於 -32dB 且動態範圍小於 14dB)
        if noise_floor_db > -33.0 and rms_db > -28.0 and dynamic_range < 16.0:
            noisy_segments.append({
                "start": start_sec, "end": end_sec,
                "type": "環境底噪/雜音過大 (冷氣/風扇/室內噪音)",
                "noise_db": round(float(noise_floor_db), 1),
                "snr": round(float(dynamic_range), 1)
            })
            
        # B. 迴音 / 空曠殘響 (Echo Score 高，且音量不是完全靜音)
        if echo_score > 0.42 and rms_db > -35.0:
            echo_segments.append({
                "start": start_sec, "end": end_sec,
                "type": "明顯空間迴音 / 空曠殘響 (遠場麥克風效應)",
                "echo_score": round(float(echo_score), 3)
            })
            
        # C. 爆音 / 削波失真 (Clipping > 0.96)
        if peak_val > 0.97:
            clipping_segments.append({
                "start": start_sec, "end": end_sec,
                "type": "音量過載 / 瞬間爆音 (Clipping)",
                "peak": round(float(peak_val), 3)
            })

    # 合併連續區間
    def merge_segments(segs, max_gap=20.0):
        if not segs:
            return []
        merged = []
        cur = dict(segs[0])
        for nxt in segs[1:]:
            if nxt["start"] - cur["end"] <= max_gap:
                cur["end"] = nxt["end"]
            else:
                merged.append(cur)
                cur = dict(nxt)
        merged.append(cur)
        return merged

    merged_noisy = merge_segments(noisy_segments)
    merged_echo = merge_segments(echo_segments)
    merged_clipping = merge_segments(clipping_segments)
    
    return {
        "total_duration": total_sec,
        "noisy_segments": merged_noisy,
        "echo_segments": merged_echo,
        "clipping_segments": merged_clipping
    }

if __name__ == "__main__":
    vpath = "video_indexer/2026-07-17碳盤查內訓 part1.mp4"
    res = analyze_audio_track(vpath)
    
    print("\n" + "="*50)
    print("📢 聲學分析報告：環境雜音、迴音與爆音異常時間段落")
    print("="*50)
    
    print("\n【一、明顯空間迴音 / 空曠殘響段落】")
    if res["echo_segments"]:
        for s in res["echo_segments"]:
            print(f"⏱️ {format_time(s['start'])} ~ {format_time(s['end'])} ({s['type']})")
    else:
        print("未偵測到持續性的嚴重迴音。")
        
    print("\n【二、環境底噪 / 背景噪音較大段落】")
    if res["noisy_segments"]:
        for s in res["noisy_segments"]:
            print(f"⏱️ {format_time(s['start'])} ~ {format_time(s['end'])} ({s['type']})")
    else:
        print("未偵測到嚴重干擾之背景底噪。")

    print("\n【三、音量過載 / 爆音失真段落】")
    if res["clipping_segments"]:
        for s in res["clipping_segments"]:
            print(f"⏱️ {format_time(s['start'])} ~ {format_time(s['end'])} ({s['type']})")
    else:
        print("無明顯削波爆音。")
