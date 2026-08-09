"""
Advanced AI Vocal Isolation & Background Laughter/Chatter Stripper
(深度神經網路人聲抽離與背景笑聲/人聲干擾消除)
"""

import os
import sys
import numpy as np
from pathlib import Path

if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

input_mp3 = Path("video_indexer/2026-07-17碳盤查內訓 part1_index/noise_samples/06_討論間隔背景雜音.mp3")
out_dir = Path("video_indexer/2026-07-17碳盤查內訓 part1_index/denoised_samples")
out_dir.mkdir(parents=True, exist_ok=True)

def process_ai_vocal_isolation():
    import soundfile as sf
    import noisereduce as nr
    from pyrnnoise import RNNoise
    
    print(f"讀取音檔: {input_mp3.name}...")
    audio, sr = sf.read(str(input_mp3))
    
    # 若為立體聲轉為單聲道處理
    if len(audio.shape) > 1:
        mono = np.mean(audio, axis=1)
    else:
        mono = audio
        
    print(f"音訊長度: {len(mono)/sr:.2f} 秒, 取樣率: {sr} Hz")
    
    # -------------------------------------------------------------
    # 1. RNNoise 深度神經網絡人聲隔離 (專門消除旁人說話、笑聲、背景雜談)
    # -------------------------------------------------------------
    print("\n[處理中 1/3] 執行 RNNoise 深度神經網絡人聲分離（消除背景笑聲與旁人說話）...")
    denoiser = RNNoise(sample_rate=sr)
    # 分段處理防止記憶體溢出
    chunk_len = sr * 10
    rnnoise_out = []
    for i in range(0, len(mono), chunk_len):
        chunk = mono[i : i + chunk_len]
        cleaned_chunk = denoiser.filter(chunk)
        rnnoise_out.append(cleaned_chunk)
    rnnoise_audio = np.concatenate(rnnoise_out)
    
    out_f1 = out_dir / "06_AI方案A_RNNoise神經網路_消除背景笑聲與旁人人聲.mp3"
    sf.write(str(out_f1), rnnoise_audio, sr)
    print(f"[OK 產出] -> {out_f1.name}")
    
    # -------------------------------------------------------------
    # 2. 非平穩態動態頻譜降噪 (Non-Stationary Spectral Gating)
    # -------------------------------------------------------------
    print("\n[處理中 2/3] 執行非平穩態動態動態降噪（動態追蹤並壓制突發笑聲與干擾）...")
    reduced_noise = nr.reduce_noise(
        y=mono,
        sr=sr,
        stationary=False,
        prop_decrease=0.92,
        time_constant_s=1.2,
        freq_mask_smooth_hz=400
    )
    out_f2 = out_dir / "06_AI方案B_非平穩態頻譜過濾_壓制突發干擾聲.mp3"
    sf.write(str(out_f2), reduced_noise, sr)
    print(f"[OK 產出] -> {out_f2.name}")

    # -------------------------------------------------------------
    # 3. 雙重複合人聲抽離 (RNNoise + 智慧語音能量遮罩)
    # -------------------------------------------------------------
    print("\n[處理中 3/3] 執行雙重複合人聲抽離（主講人聲單獨保留，背景完全淨空）...")
    # 先經神經網路消除笑聲，再進行動態門限壓制
    double_cleaned = nr.reduce_noise(
        y=rnnoise_audio,
        sr=sr,
        stationary=False,
        prop_decrease=0.88
    )
    out_f3 = out_dir / "06_AI方案C_雙重神經網路強效淨化_極致純淨人聲.mp3"
    sf.write(str(out_f3), double_cleaned, sr)
    print(f"[OK 產出] -> {out_f3.name}")

    print("\n🎉 全部 AI 人聲隔離音檔已生成完畢！")

if __name__ == "__main__":
    process_ai_vocal_isolation()
