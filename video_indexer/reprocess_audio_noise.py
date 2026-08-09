"""
Reprocess Audio Noise & Remove Background Laughter
重新精準降噪與消除背景笑聲/旁人雜談 (針對 06_討論間隔背景雜音.mp3)
"""

import os
import sys
import subprocess
import soundfile as sf
import numpy as np
import scipy.signal as signal
import noisereduce as nr

if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

input_mp3 = "video_indexer/2026-07-17碳盤查內訓 part1_index/noise_samples/06_討論間隔背景雜音.mp3"
out_dir = "video_indexer/2026-07-17碳盤查內訓 part1_index/denoised_samples"
os.makedirs(out_dir, exist_ok=True)

print(f"載入原始音訊: {input_mp3}...")
audio, sr = sf.read(input_mp3)
if len(audio.shape) > 1:
    audio = np.mean(audio, axis=1)

print(f"音訊長度: {len(audio)/sr:.2f} 秒, 取樣率: {sr} Hz")

# 1. 深度神經網路 RNNoise 處理 (消除一般聲學雜音、設備電流與空調)
temp_in = os.path.join(out_dir, "temp_raw.wav")
temp_rnn = os.path.join(out_dir, "temp_rnn.wav")
sf.write(temp_in, audio, sr)

cmd_rnn = [
    "ffmpeg", "-y", "-i", temp_in,
    "-af", "highpass=f=85,arnndn=m=video_indexer/bd.rnnn,lowpass=f=11500",
    temp_rnn
]
subprocess.run(cmd_rnn, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
rnn_audio, _ = sf.read(temp_rnn)

# 2. 頻譜噪聲底消除 (消除殘存靜態白噪聲)
cleaned_stationary = nr.reduce_noise(
    y=rnn_audio,
    sr=sr,
    stationary=True,
    prop_decrease=0.92
)

# 3. 核心人聲能量偵測與智慧主講鎖定遮罩
# 主講人聲音在 150Hz~1800Hz 具備強烈基頻與共振峰能量
b_vocal, a_vocal = signal.butter(4, [150 / (sr/2), 1800 / (sr/2)], btype='bandpass')
vocal_core = signal.filtfilt(b_vocal, a_vocal, cleaned_stationary)

frame_len = int(0.025 * sr) # 25ms
hop = int(0.010 * sr)       # 10ms
num_frames = (len(audio) - frame_len) // hop

vocal_energy = np.zeros(num_frames)
for i in range(num_frames):
    f_core = vocal_core[i*hop : i*hop + frame_len]
    rms_c = np.sqrt(np.mean(f_core**2) + 1e-12)
    vocal_energy[i] = rms_c

# 針對 59.8s ~ 65.1s (旁人笑聲與「找不到啊/哪一個」段落) 以及各主講停頓處進行精準消除
gain_strict = np.zeros(num_frames)
hold_frames = int(0.20 * sr / hop) # 200ms 釋放平滑
hold_cnt = 0

# 主講能量門檻：主講人發言 Core RMS > 0.08，背景碎嘴/笑聲 Core RMS 約 0.04~0.07
# 此外在 59.8s ~ 65.1s 特別強化靜音遮罩
for i in range(num_frames):
    t_sec = (i * hop) / sr
    # 59.8s ~ 65.1s 為旁人嬉鬧笑聲空檔
    if 59.5 <= t_sec <= 65.1:
        gain_strict[i] = 0.0
        hold_cnt = 0
        continue

    if vocal_energy[i] > 0.075:
        gain_strict[i] = 1.0
        hold_cnt = hold_frames
    elif hold_cnt > 0:
        gain_strict[i] = 1.0
        hold_cnt -= 1
    else:
        # 非主講發言時段衰減 99% (-40dB)
        gain_strict[i] = 0.005

# 平滑過渡增益曲線 (40ms crossfade 防止爆音)
gain_samples = np.interp(
    np.arange(len(audio)),
    np.arange(num_frames) * hop + frame_len // 2,
    gain_strict
)
b_sm, a_sm = signal.butter(2, 25 / (sr/2), btype='low')
smooth_gain_strict = signal.filtfilt(b_sm, a_sm, gain_samples)
smooth_gain_strict = np.clip(smooth_gain_strict, 0.0, 1.0)

# =========================================================================
# 版本 1：🌟【AI 智慧主講淨音版】（徹底消除背景笑聲、旁人雜音與環境底噪）
# =========================================================================
vocal_isolated = cleaned_stationary * smooth_gain_strict
f_ver1_wav = os.path.join(out_dir, "temp_ver1.wav")
f_ver1_mp3 = os.path.join(out_dir, "06_重新修復_方案1_AI主講語音鎖定_旁人笑聲100趴徹底消音版.mp3")
sf.write(f_ver1_wav, vocal_isolated, sr)

cmd_ver1 = [
    "ffmpeg", "-y", "-i", f_ver1_wav,
    "-af", "equalizer=f=3000:t=q:w=1.5:g=3.0,equalizer=f=350:t=q:w=2:g=-2.0,acompressor=threshold=-22dB:ratio=2.5:attack=10:release=120,loudnorm=I=-16:TP=-1.5:LRA=10",
    "-c:a", "libmp3lame", "-b:a", "192k", f_ver1_mp3
]
subprocess.run(cmd_ver1, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"[OK] 產出 -> {os.path.basename(f_ver1_mp3)}")

# =========================================================================
# 版本 2：🎧【深度神經網路去噪版】（RNNoise 全頻降噪，消除冷氣與底噪，保留自然對話）
# =========================================================================
f_ver2_wav = os.path.join(out_dir, "temp_ver2.wav")
f_ver2_mp3 = os.path.join(out_dir, "06_重新修復_方案2_深度神經網路去噪_冷氣嗡鳴與空調底噪消除版.mp3")
sf.write(f_ver2_wav, cleaned_stationary, sr)

cmd_ver2 = [
    "ffmpeg", "-y", "-i", f_ver2_wav,
    "-af", "equalizer=f=3200:t=q:w=1.5:g=2.0,acompressor=threshold=-20dB:ratio=2.0:attack=15:release=150,loudnorm=I=-16:TP=-1.5:LRA=11",
    "-c:a", "libmp3lame", "-b:a", "192k", f_ver2_mp3
]
subprocess.run(cmd_ver2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"[OK] 產出 -> {os.path.basename(f_ver2_mp3)}")

# =========================================================================
# 版本 3：🎙️【錄音室廣播級修復版】（溫潤飽滿主講人聲 + 80% 壓制旁人笑聲）
# =========================================================================
gain_soft = np.clip(smooth_gain_strict * 0.90 + 0.10, 0.0, 1.0)
vocal_soft = cleaned_stationary * gain_soft
f_ver3_wav = os.path.join(out_dir, "temp_ver3.wav")
f_ver3_mp3 = os.path.join(out_dir, "06_重新修復_方案3_錄音室廣播級修復_溫潤清晰主講人聲美化版.mp3")
sf.write(f_ver3_wav, vocal_soft, sr)

cmd_ver3 = [
    "ffmpeg", "-y", "-i", f_ver3_wav,
    "-af", "equalizer=f=2800:t=q:w=1.2:g=3.5,equalizer=f=120:t=q:w=1.0:g=2.0,acompressor=threshold=-19dB:ratio=3.0:attack=12:release=160,loudnorm=I=-16:TP=-1.5:LRA=10",
    "-c:a", "libmp3lame", "-b:a", "192k", f_ver3_mp3
]
subprocess.run(cmd_ver3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"[OK] 產出 -> {os.path.basename(f_ver3_mp3)}")

# 清理暫存檔
for t in [temp_in, temp_rnn, f_ver1_wav, f_ver2_wav, f_ver3_wav]:
    if os.path.exists(t):
        os.remove(t)

# 驗證 60s ~ 65s 能量指標
print("\n=== 🎯 驗證 60s-65s（旁人笑聲與雜談段落）降噪壓制效果 ===")
for label, p in [
    ("原始未處理音檔", input_mp3),
    ("方案1 (主講語音鎖定/笑聲100%徹底淨空)", f_ver1_mp3),
    ("方案2 (神經網路全頻除噪)", f_ver2_mp3),
    ("方案3 (錄音室廣播級修復)", f_ver3_mp3)
]:
    d, _ = sf.read(p)
    if len(d.shape) > 1:
        d = np.mean(d, axis=1)
    ch = d[int(60*sr):int(65*sr)]
    sp = d[int(65*sr):int(70*sr)]
    c_rms = np.sqrt(np.mean(ch**2))
    s_rms = np.sqrt(np.mean(sp**2))
    c_db = 20 * np.log10(c_rms + 1e-9)
    s_db = 20 * np.log10(s_rms + 1e-9)
    print(f"{label:<36s} | 60s-65s 雜音/笑聲: {c_db:6.1f} dB | 65s-70s 主講人聲: {s_db:6.1f} dB | 主講/雜音比: {s_db-c_db:5.1f} dB")

print("\n處理與驗證全部完成！")
