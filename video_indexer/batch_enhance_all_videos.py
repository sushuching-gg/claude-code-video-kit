"""
Batch Video & Audio Enhancement Engine (三部內訓長片批次母帶級降噪與音訊修復)
針對使用者指定的 3 部內訓長片：
1. 2026-07-15碳盤查內訓 part 1.mp4 (49:55)
2. 2026-07-15碳盤查內訓1 part 2.mp4 (02:21:06)
3. 2026-07-17碳盤查內訓 part1.mp4 (01:58:52)

採用【方案 3-C 錄音室母帶人聲美化版】：
- RNNoise 深度神經網絡全頻去噪 (空調/環境噪聲分離)
- 頻譜溫和底噪消除 (保留 20% 自然空氣感，無真空抽氣)
- Soft-Knee Sigmoid 柔性擴展 (80ms 超柔順過渡，平滑壓制笑聲與旁人雜談)
- 錄音室母帶 EQ (120Hz 溫暖度 + 500Hz 降濁 + 2.8kHz 清晰度)
- 光學動態壓縮 + EBU R128 (-16 LUFS) 廣播標準響度
- 產出獨立純淨 MP3 音軌，以及無損無重新編碼 remux 合成全新 MP4 影片 (-c:v copy)
"""

import os
import sys
import time
import subprocess
import shutil
import glob
from pathlib import Path
import soundfile as sf
import numpy as np
import scipy.signal as signal
import noisereduce as nr

if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())


def ensure_ffmpeg():
    if shutil.which("ffmpeg"):
        return
    localapp = os.environ.get("LOCALAPPDATA", "")
    candidates = glob.glob(os.path.join(localapp, "Microsoft", "WinGet", "Packages", "*ffmpeg*", "**", "bin"), recursive=True)
    for c in candidates:
        if os.path.exists(os.path.join(c, "ffmpeg.exe")):
            os.environ["PATH"] = c + os.pathsep + os.environ["PATH"]
            break


def format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def process_single_video(
    video_path: str,
    output_dir: str,
    model_rel_path: str = "video_indexer/bd.rnnn",
    generate_video: bool = True
):
    ensure_ffmpeg()
    video_p = Path(video_path).resolve()
    out_dir_p = Path(output_dir).resolve()
    out_dir_p.mkdir(parents=True, exist_ok=True)
    
    stem = video_p.stem
    print("\n" + "="*70)
    print(f"🎬 開始處理長片: {video_p.name}")
    print("="*70)
    
    start_time = time.time()
    
    temp_raw = out_dir_p / f"temp_{stem}_raw.wav"
    temp_rnn = out_dir_p / f"temp_{stem}_rnn.wav"
    temp_eq = out_dir_p / f"temp_{stem}_eq.wav"
    out_mp3 = out_dir_p / f"{stem}_方案3C_錄音室母帶人聲美化版.mp3"
    out_mp4 = out_dir_p / f"{stem}_已修復高清音質.mp4"
    
    # 1. 抽取音訊
    print(f"  [步驟 1/6] 從影片抽取 48kHz 高取樣率音訊...")
    cmd_extract = [
        "ffmpeg", "-y", "-i", str(video_p),
        "-vn", "-ac", "1", "-ar", "48000",
        str(temp_raw)
    ]
    subprocess.run(cmd_extract, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # 2. RNNoise 深度神經網路去噪 (使用相對路徑避免 Windows 磁碟機代號冒號問題)
    print(f"  [步驟 2/6] 執行 RNNoise 深度神經網路聲學分離 (75Hz~12.5kHz)...")
    # 將反斜線轉為正斜線，確保 FFmpeg 正確載入
    clean_model_str = model_rel_path.replace("\\", "/")
    cmd_rnn = [
        "ffmpeg", "-y", "-i", str(temp_raw),
        "-af", f"highpass=f=75,arnndn=m={clean_model_str},lowpass=f=12500",
        str(temp_rnn)
    ]
    res_rnn = subprocess.run(cmd_rnn, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res_rnn.returncode != 0:
        raise RuntimeError(f"RNNoise 處理失敗: {res_rnn.stderr.decode('utf-8', errors='ignore')}")
    
    # 3. 頻譜溫和底噪平滑
    print(f"  [步驟 3/6] 執行頻譜底噪平滑 (保留 20% 空氣質感，避免真空感)...")
    rnn_audio, sr = sf.read(str(temp_rnn))
    if len(rnn_audio.shape) > 1:
        rnn_audio = np.mean(rnn_audio, axis=1)
        
    cleaned_stationary = nr.reduce_noise(
        y=rnn_audio,
        sr=sr,
        stationary=True,
        prop_decrease=0.78
    )
    
    # 4. Soft-Knee Sigmoid 柔性擴展
    print(f"  [步驟 4/6] 執行動態 S 型柔性擴展 (80ms 超柔順過渡，平滑柔化笑聲與雜談)...")
    b_vocal, a_vocal = signal.butter(2, [200 / (sr/2), 2500 / (sr/2)], btype='bandpass')
    vocal_core = signal.filtfilt(b_vocal, a_vocal, cleaned_stationary)
    
    frame_len = int(0.04 * sr) # 40ms
    hop = int(0.01 * sr)       # 10ms
    num_frames = (len(cleaned_stationary) - frame_len) // hop
    
    vocal_energy = np.zeros(num_frames)
    for i in range(num_frames):
        f_core = vocal_core[i*hop : i*hop + frame_len]
        rms_c = np.sqrt(np.mean(f_core**2) + 1e-12)
        vocal_energy[i] = rms_c
        
    gain_curve = np.zeros(num_frames)
    for i in range(num_frames):
        e = vocal_energy[i]
        norm_e = np.clip((e - 0.03) / 0.05, 0.0, 1.0)
        gain = 0.28 + 0.72 * (norm_e ** 1.6)
        gain_curve[i] = gain
        
    b_sm, a_sm = signal.butter(2, 12 / (sr/2), btype='low')
    gain_samples = np.interp(
        np.arange(len(cleaned_stationary)),
        np.arange(num_frames) * hop + frame_len // 2,
        gain_curve
    )
    smooth_gain = signal.filtfilt(b_sm, a_sm, gain_samples)
    smooth_gain = np.clip(smooth_gain, 0.0, 1.0)
    
    expanded_audio = cleaned_stationary * smooth_gain
    sf.write(str(temp_eq), expanded_audio, sr)
    
    # 5. 錄音室三段式 EQ + 光學動態壓縮 + EBU R128 標準化匯出 MP3
    print(f"  [步驟 5/6] 套用錄音室母帶 EQ 與廣播級壓限，產出高音質 MP3...")
    cmd_out_mp3 = [
        "ffmpeg", "-y", "-i", str(temp_eq),
        "-af", "equalizer=f=2800:t=q:w=1.2:g=3.0,equalizer=f=120:t=q:w=1.0:g=2.0,equalizer=f=500:t=q:w=1.8:g=-1.0,acompressor=threshold=-19dB:ratio=2.8:attack=12:release=170,loudnorm=I=-16:TP=-1.5:LRA=10",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(out_mp3)
    ]
    subprocess.run(cmd_out_mp3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # 6. (可選) 封裝回全新 MP4 影片 (無損視訊流 copy)
    if generate_video:
        print(f"  [步驟 6/6] 合成全新高清音質 MP4 影片 (視訊流 -c:v copy 無損快速封裝)...")
        cmd_remux = [
            "ffmpeg", "-y", "-i", str(video_p), "-i", str(out_mp3),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            str(out_mp4)
        ]
        subprocess.run(cmd_remux, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
    # 清理暫存檔
    for t in [temp_raw, temp_rnn, temp_eq]:
        if t.exists():
            os.remove(t)
            
    elapsed = time.time() - start_time
    total_dur = len(cleaned_stationary) / sr
    print(f"  ✨ 【{video_p.name}】處理完成！")
    print(f"     • 原始時長: {format_time(total_dur)} ({total_dur:.1f} 秒)")
    print(f"     • 處理耗時: {elapsed:.1f} 秒 ({total_dur/elapsed:.1f} 倍速即時處理)")
    print(f"     • 產出音檔: {out_mp3.name} ({os.path.getsize(out_mp3)/(1024*1024):.1f} MB)")
    if generate_video and out_mp4.exists():
        print(f"     • 產出影片: {out_mp4.name} ({os.path.getsize(out_mp4)/(1024*1024):.1f} MB)")


def main():
    base_dir = r"H:\其他電腦\我的電腦\OneDrive\2_112淨零生活運動轉型計劃\3_資料存檔\1_115\11507內訓\課程録影"
    target_files = [
        "2026-07-15碳盤查內訓 part 1.mp4",
        "2026-07-15碳盤查內訓1 part 2.mp4",
        "2026-07-17碳盤查內訓 part1.mp4"
    ]
    
    # 輸出目錄設在專案內的 batch_enhanced 資料夾中
    out_dir = Path("video_indexer/batch_enhanced").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"開始批次處理 3 部內訓長片...")
    print(f"來源資料夾: {base_dir}")
    print(f"輸出資料夾: {out_dir}\n")
    
    for idx, fname in enumerate(target_files, 1):
        fpath = os.path.join(base_dir, fname)
        if not os.path.exists(fpath):
            print(f"⚠️ 找不到檔案: {fpath}")
            continue
        print(f"\n>>> 正在處理第 {idx}/3 部影片...")
        process_single_video(fpath, str(out_dir))
        
    print("\n" + "="*70)
    print("🎉 全部 3 部內訓長片母帶級音訊修復已全部順利完成！")
    print(f"📁 產出檔案目錄: {out_dir}")
    print("="*70)


if __name__ == "__main__":
    main()
