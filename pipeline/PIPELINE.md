# PIPELINE — 渲染管線使用說明

純 CSS/JS + Playwright + FFmpeg，已驗證可在 **Windows + Node 24** 上跑（不用 HyperFrames CLI）。

## 一次性：在 %TEMP% 安裝 Playwright（避開 GDrive / 中文路徑，GOTCHAS D-1）

```powershell
$WorkDir = "$env:TEMP\cvs-render"
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
Push-Location $WorkDir
if (-not (Test-Path package.json)) { npm init -y | Out-Null }
npm install playwright
npx playwright install chromium
Pop-Location
```

渲染時讓 Node 找得到它：
```powershell
$env:NODE_PATH = "$env:TEMP\cvs-render\node_modules"
```

## 製作一支影片的步驟

```bash
# 1. 寫 SCRIPT.md + DESIGN.md，給使用者確認（鐵律！）
# 2. 改 generate_narration.py 的 SCRIPT 陣列 → 生旁白
python generate_narration.py
# 3. 改 get_durations.py 的 SUBTITLES → 量時長
python get_durations.py
#    把輸出的 const PAGES 貼進 index.html、PAGES_TIMINGS 貼進 render.py
# 4. 找 Unsplash 圖下載到 assets/images/
# 5. 渲染
$env:NODE_PATH="$env:TEMP\cvs-render\node_modules"
python render.py     # 合成主音軌 → 錄影 → mux → final.mp4
```

## 三個必須同步的地方（不同步會音畫不對齊）

| 檔案 | 內容 | 必須等於 |
|------|------|---------|
| `index.html` 的 `PAGES[].dur` | 每頁秒數 | = `render.py` 的 `PAGES_TIMINGS[].dur` |
| `render.py` 的 `PAGES_TIMINGS` | 每頁秒數 | = `index.html` 的 `PAGES` |
| `record.cjs` 的 `waitForTimeout` | 錄製毫秒 | = 總時長 × 1000 + 800（緩衝） |

> `get_durations.py` 會幫你一次算出 PAGES 與 PAGES_TIMINGS，直接複製即可。
> 每段 page_dur = 旁白實際秒數 + tail buffer（科普約 +2.2s、教學可 +3s）。

## 常見失敗 → 修法（詳見 ../GOTCHAS.md）

| 現象 | 修法 |
|------|------|
| final.mp4 沒聲音 | mux 確認有 `-map 0:v -map 1:a`（E-2） |
| `MODULE_NOT_FOUND: playwright` | 設 `NODE_PATH` 指向 %TEMP%\cvs-render（D-2） |
| 字體變預設字 | index.html 要有 `@font-face` 指向本地 .otf（C-5） |
| 開場殘留點擊遮罩 | 用 `?render=true`，CSS 隱藏遮罩自動播放（D-3） |
| Python 印中文崩潰 | 腳本已強制 utf-8 stdout（F-1） |
| 音畫不同步 | 檢查上表三處時長是否一致 |
