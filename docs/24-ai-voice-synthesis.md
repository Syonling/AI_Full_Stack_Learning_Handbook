# 24 · AI 语音合成：文字变成素材库里的声音

> 交付里程碑 M4：输入一段故事文字，选个音色，点合成——几秒后素材库多出一条 🤖 语音。
> 本章的真正主角不是某个 TTS 工具，而是**适配器模式**：把"合成"做成可插拔的插槽，
> 今天用免费方案跑通，明天换 AI API 只改一个函数。
> 预计学习时间：3~4 小时。前置：23 章（素材入库链路）、08 章（密钥管理）、09 章（后台任务）。

---

## 学习目标

1. 理解为什么要**面向"能力"编程，而不是面向"某家供应商"编程**
2. 用 edge-tts（免费、无需 key）实现第一个合成器，跑通全链路
3. 预留好接入付费 AI API 的插槽（含密钥纪律实战）
4. 处理"合成需要几秒钟"的 UX：pending 状态 + 后台任务 + 前端轮询

---

## 1. 架构先行：合成器是一个"插槽"

你未来想用 AI API 合成（比如更自然的音色、情感控制）。但无论供应商是谁，对系统而言**能力签名不变**：

```
文本 + 音色 ──▶ [ 某个合成器 ] ──▶ 音频字节
```

所以先定义插槽，再谈实现（这就是**适配器模式**，20 章分层思想的延伸）：

```python
# services/tts.py
from typing import Protocol

class Synthesizer(Protocol):
    """合成器插槽：任何实现了这个签名的东西都能被系统使用。"""
    async def synthesize(self, text: str, voice: str) -> bytes: ...
```

系统的其余部分（路由、入库、前端）只认识这个签名——**供应商被隔离在一个文件里**。
收益立现：

- 开发/学习阶段：用免费的 edge-tts，零成本零 key
- 未来上 AI API：新写一个类，改一行"用哪个"，其余代码一字不动
- 甚至可以同时保留多个，让用户选"标准音色（免费）/ AI 音色（高级）"

---

## 2. 第一个实现：edge-tts（免费替身）

edge-tts 调用微软 Edge 浏览器的在线朗读服务：**免费、无需注册、中文音色质量意外地好**——
是开发阶段的完美替身。

```bash
pip install edge-tts
```

```python
# services/tts.py（续）
import edge_tts

# 先挑三个够用的中文音色（完整列表：命令行运行 edge-tts --list-voices）
VOICES = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",   # 女声，温暖（讲故事首选）
    "yunxi":    "zh-CN-YunxiNeural",      # 男声，清朗
    "xiaoyi":   "zh-CN-XiaoyiNeural",     # 女声，活泼
}

class EdgeTTS:
    async def synthesize(self, text: str, voice: str) -> bytes:
        voice_id = VOICES.get(voice, VOICES["xiaoxiao"])
        communicate = edge_tts.Communicate(text, voice_id)
        chunks = []
        # async for = 异步版的 for：数据是一段段从网络到达的，
        # 每到一段处理一段，等待期间不阻塞别的请求（01 章 async 的实战形态）
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)                         # 拼成完整 mp3 字节

# ★ 全项目唯一的"用哪个合成器"开关
synthesizer: Synthesizer = EdgeTTS()
```

> **要点**：edge-tts 输出的就是 mp3 字节——和 23 章上传的文件殊途同归，
> 后续入库流程可以完全复用。

---

## 3. 未来插槽：接入 AI API 长什么样

等你选定了 AI 供应商（各家 TTS API 大同小异：POST 文本，返回音频），新实现大概是这个形状：

```python
# services/tts.py（未来添加——现在只需看懂形状，不用写）
import httpx
from app.core.config import settings

class CloudAITTS:
    async def synthesize(self, text: str, voice: str) -> bytes:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.某供应商.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {settings.tts_api_key}"},  # ★ 密钥来自 .env
                json={"input": text, "voice": voice, "format": "mp3"},
                timeout=60,
            )
            resp.raise_for_status()
            return resp.content

# 切换供应商 = 改这一行：
# synthesizer: Synthesizer = CloudAITTS()
```

注意两个纪律的落点：

1. **密钥走 08 章的路**：`Settings` 加 `tts_api_key: str`（无默认值 → 忘配就启动报错），
   `.env` 存真值、`.env.example` 存假值，永不进 Git
2. **网络调用要有 timeout**：任何外部 API 都可能慢/挂，60 秒兜底

---

## 4. 合成路由：pending 状态 + 后台任务

合成一段几百字的文本要花好几秒——**绝不能让 HTTP 请求傻等**（用户以为卡死了）。
用 09 章的 BackgroundTasks + audios 表的 `status` 字段解决
（21 章建表时已备好：`'pending'` 合成中 / `'ready'` 可用 / `'failed'` 失败）。

```python
# routers/synthesize.py
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from mutagen import File as MutagenFile
from pydantic import BaseModel, Field

from app.core.config import UPLOAD_DIR               # 绝对路径常量（21 章 7.2）
from app.db.database import get_db, connect          # connect(): 后台任务自己开连接
from app.services.tts import synthesizer

router = APIRouter(tags=["synthesize"])

class SynthesizeIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)   # 上限保护成本和耗时
    voice: str = "xiaoxiao"
    title: str = Field(..., min_length=1, max_length=100)

async def run_synthesis(audio_id: int, text: str, voice: str, filename: str):
    """真正干活的后台任务：注意它有自己的数据库连接（不能用请求那个，早关了）。"""
    db = connect()
    try:
        data = await synthesizer.synthesize(text, voice)
        dest = UPLOAD_DIR / filename
        dest.write_bytes(data)
        duration = round(MutagenFile(dest).info.length, 2)
        db.execute(
            "UPDATE audios SET status='ready', duration=?, size_bytes=? WHERE id=?",
            (duration, len(data), audio_id),
        )
    except Exception:
        db.execute("UPDATE audios SET status='failed' WHERE id=?", (audio_id,))
        # logger.exception(...)  ← 03 章：堆栈进日志
    finally:
        db.commit()
        db.close()

@router.post("/synthesize", status_code=202)          # 202 Accepted：任务已受理
async def synthesize(req: SynthesizeIn, background_tasks: BackgroundTasks,
                     db=Depends(get_db)):
    filename = f"{uuid.uuid4().hex}.mp3"
    cursor = db.execute(
        """INSERT INTO audios (filename, display_name, duration, size_bytes,
                               source, status)
           VALUES (?, ?, 0, 0, 'ai', 'pending')""",    # 先占位，状态 pending
        (filename, req.title),
    )
    db.commit()
    audio_id = cursor.lastrowid
    background_tasks.add_task(run_synthesis, audio_id, req.text, req.voice, filename)
    return {"id": audio_id, "status": "pending"}       # 立即返回，不等合成
```

这套「**先占位 → 202 立返 → 后台干活 → 改状态**」的模式是所有"慢操作" API 的通用解法
（视频转码、报表导出、AI 生成……全是它）。

---

## 5. 前端：合成表单 + 轮询等待

```html
<form id="tts-form">
    <input id="tts-title" placeholder="给这段语音起个名字" required>
    <textarea id="tts-text" placeholder="输入要朗读的文字…" rows="4" required></textarea>
    <select id="tts-voice">
        <option value="xiaoxiao">晓晓（女·温暖）</option>
        <option value="yunxi">云希（男·清朗）</option>
        <option value="xiaoyi">晓伊（女·活泼）</option>
    </select>
    <button id="tts-btn">🤖 合成语音</button>
</form>
```

```javascript
// js/synthesize.js
import { refreshLibrary } from "./library.js";

const form = document.querySelector("#tts-form");
const btn = document.querySelector("#tts-btn");

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    btn.disabled = true;                      // UX：防连点
    btn.textContent = "合成中…";

    const res = await fetch("http://127.0.0.1:8000/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            title: document.querySelector("#tts-title").value,
            text: document.querySelector("#tts-text").value,
            voice: document.querySelector("#tts-voice").value,
        }),
    });
    const { id } = await res.json();

    // ── 轮询：每秒问一次"好了吗"，直到 ready/failed ──
    const timer = setInterval(async () => {
        const audio = await (await fetch(`http://127.0.0.1:8000/audios/${id}`)).json();
        if (audio.status === "pending") return;          // 还没好，下秒再问

        clearInterval(timer);
        btn.disabled = false;
        btn.textContent = "🤖 合成语音";
        if (audio.status === "ready") {
            form.reset();
            await refreshLibrary();                      // 素材库出现 🤖 新条目
        } else {
            alert("合成失败，请稍后重试");
        }
    }, 1000);
});
```

（后端补一个 `GET /audios/{id}` 单条查询——07 章的老朋友。素材库列表里
`status='pending'` 的条目显示为"合成中…"且禁用试听，一行判断的事。）

> **轮询虽土但可靠**，是异步任务反馈的第一课。将来任务多了可升级 WebSocket/SSE 推送——
> 概念先放这，需要时再学。

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| edge-tts 报网络错误 | 它调的是微软在线服务，需要联网 | 检查网络；离线环境无法使用（这正是"替身"的局限）|
| 后台任务里数据库报 closed | 用了请求的 get_db 连接 | 后台任务必须自己 connect/close（第 4 节写法）|
| 合成的记录永远 pending | 后台任务抛错没兜住 | except 里置 failed + logger.exception，去日志看堆栈 |
| 前端一直"合成中" | 轮询没处理 failed 分支 | ready/failed 都要 clearInterval |
| 中文音色读英文很怪 | 音色与语言不匹配 | 正常现象；混合文本选 zh-CN 音色即可接受 |
| 想换 AI API 时到处改代码 | 没走适配器 | 回到第 1 节——只应改 tts.py 一个文件 |

---

## 小练习（交付 M4）

1. 完成全链路：输入一段 200 字小故事 → 合成 → 素材库出现 🤖 条目 → 试听音色对不对。
2. 三个音色各合成一次同一句话，对比听感，选出你 AudioBook 的默认叙述音色。
3. 断网后发起合成，验证：记录变为 failed、前端有明确提示、uploads/ 没有残留半成品。
4. 把 `VOICES` 里换上 `edge-tts --list-voices` 里你自选的音色，体会"配置与代码分离"。
5. （架构练习，只写不跑）给 `CloudAITTS` 补全你心仪供应商的真实请求格式，
   并在 Settings/.env.example 里把 `tts_api_key` 的位置留好——未来接入时应该只需十分钟。

> 压轴一章：[25 · 时间轴编辑器](25-audio-timeline.md) —— 把素材库里的声音编排成作品。
