# AGENTS.md — VideoEditBot 工作流

> **給 AntiGravity / Claude Code / Codex 等 AI Agent 的影片製作指南。**

本 repo 提供純 CSS/JS + Playwright + FFmpeg + Edge-TTS 的全自動影片製作套件。

## 快速入口

- **Claude Code 原生入口**：[CLAUDE.md](file:///j:/%E6%88%91%E7%9A%84%E9%9B%B2%E7%AB%AF%E7%A1%AC%E7%A2%9F/%E6%A1%88%E4%BB%B6%E7%B4%A0%E6%9D%90%E5%BA%AB/VideoEditBot-antigravity/CLAUDE.md)
- **踩坑避坑清單**：[GOTCHAS.md](file:///j:/%E6%88%91%E7%9A%84%E9%9B%B2%E7%AB%AF%E7%A1%AC%E7%A2%9F/%E6%A1%88%E4%BB%B6%E7%B4%A0%E6%9D%90%E5%BA%AB/VideoEditBot-antigravity/GOTCHAS.md)
- **三類影片硬規範**：[specs/](file:///j:/%E6%88%91%E7%9A%84%E9%9B%B2%E7%AB%AF%E7%A1%AC%E7%A2%9F/%E6%A1%88%E4%BB%B6%E7%B4%A0%E6%9D%90%E5%BA%AB/VideoEditBot-antigravity/specs)
- **渲染管線手冊**：[pipeline/PIPELINE.md](file:///j:/%E6%88%91%E7%9A%84%E9%9B%B2%E7%AB%AF%E7%A1%AC%E7%A2%9F/%E6%A1%88%E4%BB%B6%E7%B4%A0%E6%9D%90%E5%BA%AB/VideoEditBot-antigravity/pipeline/PIPELINE.md)
- **完整範例 (Type 03)**：[examples/03-opus-4-8/](file:///j:/%E6%88%91%E7%9A%84%E9%9B%B2%E7%AB%AF%E7%A1%AC%E7%A2%9F/%E6%A1%88%E4%BB%B6%E7%B4%A0%E6%9D%90%E5%BA%AB/VideoEditBot-antigravity/examples/03-opus-4-8)

## 🔴 核心鐵律
**任何 code / TTS / 渲染之前，第一步一定是產出 `SCRIPT.md` 與 `DESIGN.md`，在對話中展示給使用者審查，等使用者明確說「go」才動工。**

## 系統元件就緒狀況
- **Python 3.13**：`python --version` (OK)
- **edge-tts**：已安裝 (`pip install edge-tts` OK)
- **Node.js 22 LTS**：`node --version` (OK)
- **FFmpeg 9.0**：WinGet Gyan.FFmpeg (已加入 User PATH)
- **Playwright + Chromium**：安裝於 `%TEMP%\cvs-render` (OK)
- **源石黑體**：`pipeline/fonts/GenSekiGothic2TW-*.otf` (OK)
- **母帶級音訊降噪與人聲美化**：`video_indexer/enhance_audio.py` (方案 3-C 就緒)
- **長片多模態索引搜尋引擎**：`video_indexer/indexer.py` (Whisper ASR 就緒)

