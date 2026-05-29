# claude-code-video-kit

> 給 **Claude Code** agent 用的三類影片製作 kit。自包含、可 fork、已驗證在 Windows + Node 24 跑得順。

## 一句話

把「我想做一支影片」分流到三類規範之一，依規範跑完整工作流（純 CSS/JS + Playwright + FFmpeg），最後可打包成技能。

## 為什麼是 Claude Code 專用

原始 `claude-video-specs` 用 `AGENTS.md` + `opencode.json` 當入口，給四種 agent 共用——但 **Claude Code 只自動讀 `CLAUDE.md`**，不讀 AGENTS.md，且 bash-first 工具鏈在 Windows 上常卡。這個 repo 把「Claude Code 跑得順」的版本獨立出來：入口是 `CLAUDE.md`、管線避開 HyperFrames CLI（Node 24 會 crash）、所有踩坑修法內建。

## 結構

```
claude-code-video-kit/
├── CLAUDE.md              ← Claude Code 入口（agent 自動讀，含 5 階段流程 + 鐵律）
├── GOTCHAS.md             ← 開工前必讀的踩坑清單
├── specs/                 ← 三類影片硬規範（01 活動紀錄 / 02 教學 / 03 社群科普）
├── pipeline/              ← 可重用渲染管線 + PIPELINE.md
└── examples/
    └── 03-opus-4-8/       ← 完整 03 社群科普範例（Claude Code 實作，可 fork）
```

## 三類影片

| # | 類型 | 片長 | 核心元素 |
|---|------|------|---------|
| 01 | 活動紀錄 | 60–180s | 口白 + 大字卡 + BGM 過場 |
| 02 | 教學影片 | 4–8 min | SOIL 教學脈絡 + 動畫 + TTS |
| 03 | 社群科普 | 2–3 min | 強 Hook + 多版面 + 照片佐證 |

## 快速開始

1. 用 Claude Code 打開本 repo（它會自動讀 `CLAUDE.md`）
2. 跟它說「我要做一支社群科普影片」
3. 依 5 階段流程走：環境檢查 → 選類型 → **先給 SCRIPT.md + DESIGN.md** → 試作 → 調整 → 打包

> 不含任何 binary 素材（mp4 / mp3 / 字體 / 圖片）——全由 bootstrap 動態取得，範例也只保留文字與程式碼。

## 參考範例

`examples/03-opus-4-8/` 是一支實際完成的 2:30 社群科普影片（主題：Claude Opus 4.8 發布），13 頁、6 種版面全用上、純 SVG 自繪動畫。含 `SCRIPT.md`、`DESIGN.md`、`index.html`，可直接 fork 改主題。
