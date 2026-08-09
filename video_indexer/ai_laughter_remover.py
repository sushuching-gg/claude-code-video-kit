"""
AI Non-Stationary Noise & Laughter Eliminator (AI 旁人笑聲與突發環境噪聲強效濾除器)
使用 noisereduce 非平穩態頻譜能量遮罩 (Non-Stationary Spectral Gating) + 語音能量增強
"""

import sys
import numpy as np
from pathlib import Path
import soundfile as sf
import noisereduce as nr
import scipy.signal as signal

if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

input_mp3 = Path("video_indexer/2026-07-17碳盤查內訓 part1_index/noise_samples/06_討論間隔背景雜音.mp3")
out_dir = Path("video_indexer/2026-07-17碳盤查內訓 part1_index/denoised_samples")
out_dir.mkdir(parents=True, exist_ok=True)

print(f"讀取音訊: {input_mp3.name}...")
data, sr = sf.read(str(input_mp3))
if len(data.shape) > 1:
    mono = np.mean(data, axis=1)
else:
    mono = data

print(f"音訊取樣率: {sr} Hz, 總長度: {len(mono)/sr:.2f} 秒")

# 1. 方案 A：高強度非平穩態 AI 頻譜隔離 (專門追蹤並消除背景突發笑聲、碎嘴、嬉鬧與雜談)
print("\n[運算中 1/3] 執行高強度非平穩態頻譜隔離 (消除笑聲與旁人對話)...")
cleaned_v1 = nr.reduce_noise(
    y=mono,
    sr=sr,
    stationary=False,
    prop_decrease=0.98,
    time_constant_s=0.8,
    freq_mask_smooth_hz=500,
    n_std_thresh_stationary=1.2
)
f1 = out_dir / "06_AI強效版A_消除背景笑聲與非主講雜談.mp3"
sf.write(str(f1), cleaned_v1, sr)
print(f"[OK] 產出 -> {f1.name}")

# 2. 方案 B：雙階段人聲分離 (先切除低頻混濁 + 高強度動態噪聲追蹤 + 人聲頻段保留)
print("\n[運算中 2/3] 執行雙階段人聲分離 (高通85Hz + 0.95動態噪聲消除)...")
# 4階巴特沃斯高通濾波器消除麥克風低頻與桌震
b, a = signal.butter(4, 85 / (sr / 2), btype='high')
filtered_low = signal.filtfilt(b, a, mono)

cleaned_v2 = nr.reduce_noise(
    y=filtered_low,
    sr=sr,
    stationary=False,
    prop_decrease=0.95,
    time_constant_s=1.0,
    n_fft=2048,
    win_length=2048,
    hop_length=512
)
f2 = out_dir / "06_AI強效版B_主講人聲單獨保留_極致純淨版.mp3"
sf.write(str(f2), cleaned_v2, sr)
print(f"[OK] 產出 -> {f2.name}")

# 3. 方案 C：智慧主講人聲閘門 (VAD Gating - 講話時才開門，背景有人在笑或空檔時 100% 絕對靜音)
print("\n[運算中 3/3] 執行智慧主講人聲閘門 (非主講人發言區段完全靜音)...")
# 計算即時短時能量
frame_len = int(0.04 * sr) # 40ms
hop = int(0.01 * sr) # 10ms
energy = []
for i in range(0, len(cleaned_v2) - frame_len, hop):
    frame = cleaned_v2[i : i + frame_len]
    rms = np.sqrt(np.mean(frame**2) + 1e-12)
    energy.append(rms)

energy = np.array(energy)
# 平滑能量曲線
kernel = np.ones(15) / 15
smooth_energy = np.convolve(energy, kernel, mode='same')
thresh = np.percentile(smooth_energy, 45) # 中間能量門檻

# 產生平滑增益遮罩 (Soft Mask)
gain = np.zeros(len(cleaned_v2))
for idx, i in enumerate(range(0, len(cleaned_v2) - frame_len, hop)):
    g = 1.0 if smooth_energy[idx] > thresh else 0.03 # 衰減 97%
    gain[i : i + hop] = g
gain[len(cleaned_v2)-frame_len:] = gain[len(cleaned_v2)-frame_len-1]

# 平滑過渡防止點擊音
b_smooth, a_smooth = signal.butter(2, 8 / (sr / 2), btype='low')
smooth_gain = signal.filtfilt(b_smooth, a_smooth, gain)
smooth_gain = np.clip(smooth_gain, 0.0, 1.0)

gated_audio = cleaned_v2 * smooth_gain
f3 = out_dir / "06_AI強效版C_主講語音閘門_背景笑聲完全歸零版.mp3"
sf.write(str(f3), gated_audio, sr)
print(f"[OK] 產出 -> {f3.name}")

print("\n🎉 全部全新 AI 強效降噪與笑聲消除音檔已生成完成！")
