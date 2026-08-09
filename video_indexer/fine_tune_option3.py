"""
Fine-tuned Option 3 Audio Polish Engine (方案 3 進階優化版)
針對使用者回饋：杜絕切斷感/真空感，保留自然空間連續性，精緻柔化背景笑聲與雜音，提升主講人聲質感。
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

# 1. 深度神經網絡 RNNoise 全頻噪聲分離 (溫和處理，保留空間感)
temp_in = os.path.join(out_dir, "temp_raw_opt3.wav")
temp_rnn = os.path.join(out_dir, "temp_rnn_opt3.wav")
sf.write(temp_in, audio, sr)

cmd_rnn = [
    "ffmpeg", "-y", "-i", temp_in,
    "-af", "highpass=f=75,arnndn=m=video_indexer/bd.rnnn,lowpass=f=12500",
    temp_rnn
]
subprocess.run(cmd_rnn, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
rnn_audio, _ = sf.read(temp_rnn)

# 2. 溫和頻譜降噪 (去除持續性冷氣高頻沙沙聲與低頻嗡嗡聲，保留 20% 環境空氣底色避免死寂感)
cleaned_stationary = nr.reduce_noise(
    y=rnn_audio,
    sr=sr,
    stationary=True,
    prop_decrease=0.78 # 溫和降噪，不產生金屬破音或空洞感
)

# 3. 連續多頻帶動態擴展（無階躍切斷，平滑呼吸過渡）
# 提取語音核心頻段 (200Hz ~ 2500Hz)
b_vocal, a_vocal = signal.butter(2, [200 / (sr/2), 2500 / (sr/2)], btype='bandpass')
vocal_core = signal.filtfilt(b_vocal, a_vocal, cleaned_stationary)

frame_len = int(0.04 * sr) # 40ms 窗口
hop = int(0.01 * sr)       # 10ms 步長
num_frames = (len(audio) - frame_len) // hop

vocal_energy = np.zeros(num_frames)
for i in range(num_frames):
    f_core = vocal_core[i*hop : i*hop + frame_len]
    rms_c = np.sqrt(np.mean(f_core**2) + 1e-12)
    vocal_energy[i] = rms_c

# 計算平滑擴展增益曲線 (柔性向下擴展，最大衰減僅 12dB~16dB，絕無完全靜音)
gain_curve_A = np.zeros(num_frames)
gain_curve_B = np.zeros(num_frames)
gain_curve_C = np.zeros(num_frames)

for i in range(num_frames):
    e = vocal_energy[i]
    # 柔和 S 型過渡 (Soft-Knee Sigmoid Expansion)
    # 方案 3-A: 溫潤自然版 (衰減底限 0.35 = 約 -9dB，極致自然平滑)
    norm_e = np.clip((e - 0.03) / 0.05, 0.0, 1.0)
    gain_A = 0.35 + 0.65 * (norm_e ** 1.5)
    gain_curve_A[i] = gain_A

    # 方案 3-B: 多頻帶笑聲柔化聚焦版 (衰減底限 0.20 = 約 -14dB，針對 59.8-65s 笑聲柔化)
    t_sec = (i * hop) / sr
    if 59.5 <= t_sec <= 65.1:
        # 笑聲空檔平滑壓低為遠處微弱聲響，不切斷
        gain_B = 0.15 + 0.25 * norm_e
    else:
        gain_B = 0.25 + 0.75 * (norm_e ** 1.8)
    gain_curve_B[i] = gain_B

    # 方案 3-C: 錄音室母帶人聲美化版 (衰減底限 0.28 = 約 -11dB，人聲動態提升)
    gain_C = 0.28 + 0.72 * (norm_e ** 1.6)
    gain_curve_C[i] = gain_C

# 平滑過渡增益曲線 (80ms 超柔順濾波器，徹底消除抽氣感與階躍感)
b_sm, a_sm = signal.butter(2, 12 / (sr/2), btype='low')

def apply_smooth_gain(gain_c):
    gain_samples = np.interp(
        np.arange(len(audio)),
        np.arange(num_frames) * hop + frame_len // 2,
        gain_c
    )
    sm_gain = signal.filtfilt(b_sm, a_sm, gain_samples)
    return np.clip(sm_gain, 0.0, 1.0)

smooth_gain_A = apply_smooth_gain(gain_curve_A)
smooth_gain_B = apply_smooth_gain(gain_curve_B)
smooth_gain_C = apply_smooth_gain(gain_curve_C)

# =========================================================================
# 方案 3-A：【溫潤自然廣播版】（極致平滑空間感，無任何切斷感，冷氣消音，笑聲柔化）
# =========================================================================
audio_3A = cleaned_stationary * smooth_gain_A
f_3A_wav = os.path.join(out_dir, "temp_3A.wav")
f_3A_mp3 = os.path.join(out_dir, "06_方案3優化A_溫潤自然廣播版_無切斷感_空間連續平滑.mp3")
sf.write(f_3A_wav, audio_3A, sr)

cmd_3A = [
    "ffmpeg", "-y", "-i", f_3A_wav,
    "-af", "equalizer=f=2600:t=q:w=1.2:g=2.5,equalizer=f=380:t=q:w=2.0:g=-1.5,acompressor=threshold=-18dB:ratio=2.2:attack=20:release=200,loudnorm=I=-16:TP=-1.5:LRA=11",
    "-c:a", "libmp3lame", "-b:a", "192k", f_3A_mp3
]
subprocess.run(cmd_3A, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"[OK] 產出 -> {os.path.basename(f_3A_mp3)}")

# =========================================================================
# 方案 3-B：【進階多頻帶人聲聚焦版】（主講人聲立體通透，笑聲壓低為遠景微弱背景）
# =========================================================================
audio_3B = cleaned_stationary * smooth_gain_B
f_3B_wav = os.path.join(out_dir, "temp_3B.wav")
f_3B_mp3 = os.path.join(out_dir, "06_方案3優化B_多頻帶人聲聚焦版_笑聲壓低柔化_主講清晰立體.mp3")
sf.write(f_3B_wav, audio_3B, sr)

cmd_3B = [
    "ffmpeg", "-y", "-i", f_3B_wav,
    "-af", "equalizer=f=3000:t=q:w=1.5:g=3.2,equalizer=f=150:t=q:w=1.0:g=1.5,acompressor=threshold=-20dB:ratio=2.6:attack=15:release=180,loudnorm=I=-16:TP=-1.5:LRA=10",
    "-c:a", "libmp3lame", "-b:a", "192k", f_3B_mp3
]
subprocess.run(cmd_3B, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"[OK] 產出 -> {os.path.basename(f_3B_mp3)}")

# =========================================================================
# 方案 3-C：【錄音室母帶級人聲美化版】（溫暖胸腔共鳴 + 柔和光澤感 + 廣播級平滑壓限）
# =========================================================================
audio_3C = cleaned_stationary * smooth_gain_C
f_3C_wav = os.path.join(out_dir, "temp_3C.wav")
f_3C_mp3 = os.path.join(out_dir, "06_方案3優化C_錄音室母帶人聲美化版_厚實溫暖_高階平衡.mp3")
sf.write(f_3C_wav, audio_3C, sr)

cmd_3C = [
    "ffmpeg", "-y", "-i", f_3C_wav,
    "-af", "equalizer=f=2800:t=q:w=1.2:g=3.0,equalizer=f=120:t=q:w=1.0:g=2.0,equalizer=f=500:t=q:w=1.8:g=-1.0,acompressor=threshold=-19dB:ratio=2.8:attack=12:release=170,loudnorm=I=-16:TP=-1.5:LRA=10",
    "-c:a", "libmp3lame", "-b:a", "192k", f_3C_mp3
]
subprocess.run(cmd_3C, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"[OK] 產出 -> {os.path.basename(f_3C_mp3)}")

# 清理暫存檔
for t in [temp_in, temp_rnn, f_3A_wav, f_3B_wav, f_3C_wav]:
    if os.path.exists(t):
        os.remove(t)

# 驗證聽感能量指標
print("\n=== 🎯 驗證方案 3 系列在 60s-65s（旁人笑聲雜談）與 65s-70s（主講人聲）的平滑度與能量 ===")
for label, p in [
    ("原始未處理音檔", input_mp3),
    ("方案 3-A (溫潤自然廣播版)", f_3A_mp3),
    ("方案 3-B (多頻帶人聲聚焦版)", f_3B_mp3),
    ("方案 3-C (錄音室母帶人聲美化版)", f_3C_mp3)
]:
    d, _ = sf.read(p)
    if len(d.shape) > 1:
        d = np.mean(d, axis=1)
    ch = d[int(60*sr):int(65*sr)]
    sp = d[int(65*sr):int(70*sr)]
    gap = d[int(70*sr):int(71.5*sr)]
    c_db = 20 * np.log10(np.sqrt(np.mean(ch**2)) + 1e-9)
    s_db = 20 * np.log10(np.sqrt(np.mean(sp**2)) + 1e-9)
    g_db = 20 * np.log10(np.sqrt(np.mean(gap**2)) + 1e-9)
    print(f"{label:<32s} | 笑聲雜音區: {c_db:5.1f} dB | 主講人聲: {s_db:5.1f} dB | 停頓自然底色: {g_db:5.1f} dB | 人聲/雜音差: {s_db-c_db:4.1f} dB")

print("\n🎉 方案 3 系列精修完成！")
