# Claude Opus 4.8 的真正突破 — 社群科普影片（Claude Code 產出）

本 repo 母版第一支由 **Claude Code** 完成的影片，遵循 `specs/03-社群科普影片.md`。

- **片長**：181 秒（~3:01）· **13 頁** · 6 種版面全用上
- **主題**：Claude Opus 4.8 發布（2026-05-28），主軸「真突破不是更聰明，是更可信」
- **事實來源**：Anthropic 官方公告 + Axios / TechCrunch / 9to5Mac 交叉確認
- **素材**：Unsplash 2 張（tech.jpg / office.jpg，本地化）+ 純 SVG 自繪動畫（時間軸 / subagent 放射 / Effort 滑桿），零 AI 生圖
- **管線**：純 CSS/JS + Playwright + FFmpeg（**不用 HyperFrames CLI**，避開 Node 24 crash）

## 檔案
- `SCRIPT.md` — 5 段敘事逐頁腳本（旁白 + 字幕 + 版面 + 動畫）
- `DESIGN.md` — 視覺規範 + 避坑對照表
- `generate_narration.py` — Edge-TTS 序列生成 13 段旁白
- `get_durations.py` — 量測旁白時長，輸出 PAGES 時長表
- `index.html` — 13 頁多版面動畫骨架（`?render=true` 自動播放）
- `record.cjs` — Playwright 錄製 181.8s 無聲 webm
- `render.py` — 一鍵：合成主音軌 → 錄影 → mux 成 final.mp4
- `final.mp4` — 成品

## 重現步驟
```bash
python generate_narration.py          # 生旁白
python get_durations.py               # 取得時長（同步到 index.html / render.py 的 PAGES）
$env:NODE_PATH="$env:TEMP\cvs-render\node_modules"
python render.py                      # 合成音軌 → 錄影 → mux
```

## 避坑紀錄（對應 GOTCHAS）
| 措施 | 對應 |
|------|------|
| 不用 HyperFrames CLI，純 CSS/JS | C-4（Node 24 crash） |
| ffmpeg mux 加 `-map 0:v -map 1:a` | E-2（沒聲音） |
| node_modules 在 `%TEMP%\cvs-render`，NODE_PATH 指過去 | D-1 / D-2 |
| HTML 內 `@font-face` 指向本地 .otf | C-5（字體不顯示） |
| `?render=true` 隱藏遮罩自動播放 | D-3（開場殘影） |
| Python 強制 utf-8 輸出 | F-1（CP950） |
