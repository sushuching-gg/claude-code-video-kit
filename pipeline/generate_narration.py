# Edge-TTS 序列生成 13 段旁白（Claude Opus 4.8 科普影片）
# 執行：python generate_narration.py
import asyncio, edge_tts
from pathlib import Path

OUT = Path(__file__).parent / "assets" / "narration"
OUT.mkdir(parents=True, exist_ok=True)

VOICE = "zh-TW-YunJheNeural"
RATE = "-8%"
PITCH = "-2Hz"

SCRIPT = [
    (1,  "Anthropic 又丟出新模型，Claude Opus 4.8。但這次真正的突破，不是它變得更聰明。"),
    (2,  "誇張的是速度。上一版 Opus 4.7 才推出 41 天，4.8 就來了。AI 模型的升級，正在快到讓人跟不上。"),
    (3,  "你可以把 AI 想成一個員工。以前的版本，有點像愛逞強的新人，不懂也要硬答。4.8 更像一個資深同事：不確定的時候，它會直接跟你說。"),
    (4,  "官方說，它有更敏銳的判斷、對自己的進度更誠實，也更能獨立把長任務做完。簡單說：會標不確定、不亂吹進度、抓得到重點。"),
    (5,  "而且價格沒漲，跟 4.7 一樣，每百萬 token 五塊美金進、二十五塊出。能力升級，但你不用多付錢。"),
    (6,  "最有感的新功能叫 Dynamic Workflow。它能在一個對話裡，同時派出數百個子代理分頭做事，再把結果收回來。跨幾十萬行程式碼的大改造，一次搞定。"),
    (7,  "還多了一個努力旋鈕。趕時間就調低，快速給答案；要它仔細想就調高，多花一點時間換更深的思考。深度，你說了算。"),
    (8,  "再搭上 Fast Mode：速度快兩倍半，成本比舊版便宜三倍。要快、要省、要好，這次比較不用三選二。"),
    (9,  "但回到最開頭。這一代真正的突破，是可信度。它讓程式碼裡的缺陷溜過去、不出聲的機率，降到大約只剩四分之一。"),
    (10, "分數當然也有進步。實戰級的程式任務，從六成四提升到接近七成；而它更是第一個在不照搬錯誤結果這項，拿到零失誤的 Claude。"),
    (11, "所以你可以這樣用：一般任務開 Fast Mode 省錢；遇到難題把 Effort 調高；要動大型專案，就交給 Dynamic Workflow 一次跑完。"),
    (12, "所以 AI 的下一步，可能不是更會講話，而是更敢承認自己不知道。一個會喊停的 AI，才是真的能託付工作的 AI。"),
    (13, "而這還不是終點。Anthropic 說，更強的 Mythos 級模型，數週內就會登場。"),
]

async def synth(i, text):
    out = OUT / f"page-{i:02d}.mp3"
    c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await c.save(str(out))
    print(f"OK page-{i:02d}.mp3")

async def main():
    for i, t in SCRIPT:
        for r in range(3):
            try:
                await synth(i, t); break
            except Exception as e:
                print(f"retry {i} ({r+1}): {e}")
                await asyncio.sleep(2)
    print("All done.")

if __name__ == "__main__":
    asyncio.run(main())
