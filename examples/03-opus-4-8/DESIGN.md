# DESIGN — Claude Opus 4.8 的真正突破（Type 03 社群科普）

> 套用 03-社群科普影片規範視覺系統，沿用本 repo 既有 antigravity_context_output 的視覺基礎，
> 確保跨 agent 風格一致；本片為 **Claude Code** 產出。

---

## 核心字體

源石黑體 `GenSekiGothic2TW`（H 900 重黑 / B 700 粗體 / M 500 中黑）
- 標題與金句統一使用 `GenSekiGothic2TW-H` 重黑，展現力量感與高辨識度。
- 正文使用 `GenSekiGothic2TW-M`，字幕使用 `-B` 粗體。
- HTML `<style>` 內以 `@font-face` 指向本地 `assets/fonts/*.otf`（GOTCHAS C-5）。

---

## 核心配色（沿用 repo 標準，未自創）

| 色樣 | HEX | 用法 |
|------|------|------|
| 紙張米白 | `#FAF7EE` | 內容頁背景，溫潤紙感 |
| 墨黑文字 | `#1A1A1A` | 文字 / L5 黑底高對比 |
| 強調綠 (Teal) | `#0E7C7B` | 主強調（時間軸、節點、滑桿、框線發光） |
| 強調橘 (Coral) | `#E36414` | 副強調（Hook 懸念、反轉、舊數字 64.3%） |
| 社群霓虹黃 (Neon) | `#FFD23F` | 點睛（純黑大字發光、新數字 69.2%、金句、進度條末端） |

---

## 版面庫（全片整合 6 種版面）

| 版面 | 名稱 | 適用頁碼 |
|------|------|------|
| **L1** | 全版照片加暗 overlay | P2（41 天迭代） |
| **L2** | 左右非對稱分欄（左圖右文 / 左 SVG 右文） | P3（員工比喻）、P7（Effort 滑桿） |
| **L3** | 卡片圖示陣列 3×1 | P4（三可信訊號）、P11（三個你用得到） |
| **L4** | SVG 中置聚焦動畫 | P5（41 天時間軸）、P6（subagent 放射） |
| **L5** | 純大字黑底（懸念／反轉／金句／封底） | P1、P9、P12、P13 |
| **L6** | 數據左右強對比並排 | P8（Fast Mode）、P10（Benchmark 躍升） |

> 相鄰兩頁不重複版面；L5 用於 Hook / 反轉 / 金句 / 結尾共 4 次。

---

## 黃金字級階梯（社群專用大字階）

- **Hook / 反轉大字 (L5)**：`150px` → `96px`；金句 `120px`
- **頁面主標題**：`96px`
- **分欄 / 內文標題**：`64px`
- **卡片內文**：`56px`
- **對比大數字 (L6)**：`120–130px`
- **字幕字級**：`36px`（社群放大 6px），`rgba(26,26,26,0.92)` 圓角半透明墨黑底框，`bottom: 80px`

---

## 媒體素材策略

- **Unsplash 直連照片**（下載到本地 `assets/images/`，不外部依賴；用 `images.unsplash.com/photo-XXX`，非已棄用的 source.unsplash.com）：
  - `tech.jpg` — 科技 / 速度感（P2 全版背景，暗化 0.6 overlay）
  - `office.jpg` — 辦公室同事 / 協作（P3 左欄，右側 linear-gradient 淡出接文字）
- **SVG 純程式自繪動畫**（零 AI 生圖，可被其他 agent 完整複製）：
  - **時間軸**（P5）：`stroke-dasharray` 逐步繪線，4.7 / 4.8 兩節點先後發光。
  - **subagent 放射**（P6）：中央主節點脈動，放射線逐條繪出，外圈節點批次點亮後收斂。
  - **Effort 滑桿**（P7）：滑塊由 low 緩動到 high，軌道 teal→neon 漸層。

---

## 字幕與音軌規範

- **單行字幕**：不換行為最高原則，每段 ≤ 25 字（GOTCHAS B-1）。
- **字幕位置**：`bottom: 80px`、`36px`、`-B` 粗體、半透明墨黑底框。
- **旁白人聲**：Edge-TTS `zh-TW-YunJheNeural`，`rate -8% / pitch -2Hz`，100% 音量。

---

## 微動畫與節奏

- **Ken Burns 緩推**：L1 / L2 的照片在展示期間 `0.02%/s` 緩慢縮放平移，畫面有呼吸感。
- **數值飛躍（Counter / Scale）**：P8、P10 的大數字 Scale 彈出，新數字（69.2%、便宜 3 倍）帶 Neon 外框。
- **SVG 發光線條**：時間軸與 subagent 放射線用 `stroke-dasharray` 逐步繪製。
- **進度條**：頂部 `8px`，`linear-gradient(90deg, teal, neon)`（規範第 9 章）。

---

## 已內建的避坑措施（對應你昨天的兩個卡點）

| 昨天的問題 | 本設計如何避開 | 對應 GOTCHAS |
|-----------|---------------|-------------|
| 渲染 crash | **不用 HyperFrames CLI**，純 CSS/JS + Playwright（Node 24 安全） | C-4 |
| 成品沒聲音 | ffmpeg mux 強制 `-map 0:v:0 -map 1:a:0` | E-2 |
| （預防）淡出爆掉 | BGM 淡出用 `afade=...:st=`（秒）非 `ss` | E-1 |
| （預防）中文路徑 | render / node_modules 全在 `%TEMP%\cvs-render\`，產出再 copy 回 | D-1 / E-3 |
| （預防）字體不顯示 | HTML 內 `@font-face` 指向本地 .otf | C-5 |
