# 影片內容分析與智慧搜尋索引工具 (Video Indexer & Search Toolkit)

本模組為本地端影片內容分析與多模態索引套件，支援對任何既有影片（mp4, mkv, mov, webm 等）進行自動化拆解、文字辨識、影格抽樣與即時搜尋播放。

---

## 🌟 核心功能

1. 🎙️ **語音轉逐字稿與時間戳索引 (Offline Speech-to-Text ASR)**
   - 採用高效能 `faster-whisper`，免聯網即可將影片對白轉換為帶有準確 `start` / `end` 秒數的時間戳文字。
   - 支援微型模型（`tiny`）、標準模型（`base`）至高精準模型（`small` / `medium`）。
2. 🖼️ **智慧關鍵影格抽樣 (Keyframe & Scene Detection)**
   - 透過 FFmpeg 依指定時間間隔（例如每 4 秒）自動抽樣縮圖，建立可點擊的時間軸縮圖清單。
3. ⏱️ **影片中繼資料讀取 (Metadata Extraction)**
   - 透過 FFprobe 提取片長、解析度、FPS、影片/音訊編碼、內建章節等。
4. 🌐 **互動式搜尋播放器 (Search UI Player)**
   - 自動生成獨立的 `search_ui.html`，具備即時關鍵字搜尋、高亮標記、縮圖瀏覽，**點擊任何對白或縮圖即可自動跳轉至該秒數播放**。
5. 🔍 **CLI 命令列快速搜尋 (`search.py`)**
   - 終端機內一行指令檢索影片所有對白關鍵字。

---

## 🚀 快速使用

### 1. 為影片建立索引與搜尋播放器
```bash
python video_indexer/indexer.py <影片路徑> [模型大小] [縮圖抽樣秒數]
```

**範例**：
```bash
python video_indexer/indexer.py examples/03-opus-4-8/final.mp4 base 4.0
```

執行後會自動在影片同目錄（或指定資料夾）產出：
- `keyframes/`：抽樣關鍵影格縮圖目錄
- `video_index.json`：結構化全文本與時間戳索引資料
- `search_ui.html`：雙擊即可在瀏覽器開啟的智慧檢索播放器

### 2. 在終端機快速搜尋關鍵字
```bash
python video_indexer/search.py <video_index.json 路徑> <關鍵字>
```

**範例**：
```bash
python video_indexer/search.py examples/03-opus-4-8/final_index/video_index.json "突破"
```

### 3. 錄音室母帶級人聲美化與環境降噪 (`enhance_audio.py`)
採用神經網絡 RNNoise + 溫和頻譜底噪平滑 + Soft-Knee Sigmoid 人聲擴展 + 廣播級 EQ/壓限：
```bash
python video_indexer/enhance_audio.py <輸入音訊或影片路徑> [-o 輸出路徑]
```

**範例**：
```bash
python video_indexer/enhance_audio.py "video_indexer/2026-07-17碳盤查內訓 part1.mp4" -o "part1_enhanced.mp3"
```

