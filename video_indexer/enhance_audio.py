"""
Studio Master Audio Enhancer & Denoising Engine (錄音室母帶級人聲美化與環境降噪引擎)
採用使用者選定之最優方案【3-C 錄音室母帶人聲美化版】：
1. 85Hz 高通 + 12.5kHz 低通 + RNNoise 深度神經網絡全頻特徵分離
2. 溫和頻譜降噪 (保留 20% 環境空氣底色，杜絕真空抽氣感)
3. Soft-Knee Sigmoid 柔性向下擴展 (衰減底限 0.28，80ms 超柔順平滑過渡)
4. 錄音室三段式參數 EQ (120Hz 溫暖度 + 500Hz 降濁 + 2.8kHz 清晰度)
5. 廣播級光學壓縮與 EBU R128 響度標準化 (-16 LUFS)
"""

import os
import sys
import argparse
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


def enhance_audio_file(input_path: str, output_path: str, model_path: str = "video_indexer/bd.rnnn"):
    ensure_ffmpeg()
    input_p = Path(input_path).resolve()
    output_p = Path(output_path).resolve()
    output_p.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[1/5] 正在讀取輸入音訊: {input_p.name}...")
    
    # 抽取或讀取 PCM 音訊
    temp_raw = output_p.parent / f"temp_raw_{output_p.stem}.wav"
    temp_rnn = output_p.parent / f"temp_rnn_{output_p.stem}.wav"
    temp_eq = output_p.parent / f"temp_eq_{output_p.stem}.wav"
    
    cmd_extract = [
        "ffmpeg", "-y", "-i", str(input_p),
        "-vn", "-ac", "1", "-ar", "48000",
        str(temp_raw)
    ]
    subprocess.run(cmd_extract, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # 1. RNNoise 深度神經網絡全頻降噪
    print("[2/5] 執行 RNNoise 深度神經網絡聲學分離...")
    clean_model_str = model_path.replace("\\", "/")
    cmd_rnn = [
        "ffmpeg", "-y", "-i", str(temp_raw),
        "-af", f"highpass=f=75,arnndn=m={clean_model_str},lowpass=f=12500",
        str(temp_rnn)
    ]
    subprocess.run(cmd_rnn, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # 2. 載入並進行頻譜溫和底噪消除
    print("[3/5] 執行頻譜空間底噪柔化 (保留 20% 環境空氣底色)...")
    rnn_audio, sr = sf.read(str(temp_rnn))
    if len(rnn_audio.shape) > 1:
        rnn_audio = np.mean(rnn_audio, axis=1)
        
    cleaned_stationary = nr.reduce_noise(
        y=rnn_audio,
        sr=sr,
        stationary=True,
        prop_decrease=0.78
    )
    
    # 3. Soft-Knee Sigmoid 柔性向下擴展 (80ms 超柔順過渡)
    print("[4/5] 執行動態 S 型人聲擴展 (平滑壓制笑聲與旁人雜音，杜絕抽氣感)...")
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
        
    # 80ms 超平滑濾波
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
    
    # 4. 錄音室三段式 EQ + 光學動態壓縮 + EBU R128 響度標準化
    print(f"[5/5] 套用錄音室母帶 EQ 與廣播級壓限，匯出至: {output_p.name}...")
    cmd_out = [
        "ffmpeg", "-y", "-i", str(temp_eq),
        "-af", "equalizer=f=2800:t=q:w=1.2:g=3.0,equalizer=f=120:t=q:w=1.0:g=2.0,equalizer=f=500:t=q:w=1.8:g=-1.0,acompressor=threshold=-19dB:ratio=2.8:attack=12:release=170,loudnorm=I=-16:TP=-1.5:LRA=10",
        "-c:a", "libmp3lame" if output_p.suffix.lower() == ".mp3" else "pcm_s16le",
        "-b:a", "192k" if output_p.suffix.lower() == ".mp3" else None,
        str(output_p)
    ]
    cmd_out = [c for c in cmd_out if c is not None]
    subprocess.run(cmd_out, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # 清理暫存檔
    for t in [temp_raw, temp_rnn, temp_eq]:
        if t.exists():
            os.remove(t)
            
    print(f"✨ 處理完成！已產出高品質母帶級音檔 -> {output_p}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="錄音室母帶級人聲美化與環境降噪引擎 (方案 3-C)")
    parser.add_argument("input", help="輸入音訊或影片檔案路徑")
    parser.add_argument("-o", "--output", help="輸出音訊檔案路徑 (預設為 [原檔名]_enhanced_3c.mp3)")
    parser.add_argument("-m", "--model", default="video_indexer/bd.rnnn", help="RNNoise 模型路徑")
    
    args = parser.parse_args()
    out = args.output
    if not out:
        in_p = Path(args.input)
        out = str(in_p.parent / f"{in_p.stem}_enhanced_3c.mp3")
        
    enhance_audio_file(args.input, out, args.model)
