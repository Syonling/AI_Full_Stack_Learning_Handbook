# 25 · 时间轴编辑器（毕业项目压轴）

> 交付里程碑 M5，也是整个学习系统的毕业设计：把素材库的音频**拖到时间轴上编排**、
> 保存到数据库、刷新后还在、点播放完整听完你的作品。
> 预计学习时间：6~8 小时（本书最难一章，但每一步都可独立验收——严格按阶梯走）。
> 前置：22（播放器）、23（素材库）、15 章事件部分要非常熟。

---

## 学习目标

1. 建立时间轴的**坐标系思维**：像素 ⇄ 秒 的双向换算是一切的地基
2. 第一步永远是**静态渲染**：给定数据画出时间轴（不碰拖拽）
3. 用 **Pointer Events 三事件**实现拖动，含边界限制与网格吸附
4. 设计保存/加载接口（整体替换 + 事务）
5. 实现**串播调度器**：让整条时间轴按编排播放，播放头同步移动
6. 知道之后往哪进阶（裁剪、多轨、Web Audio、导出）

---

## 0. 阶梯总览（迷路时回来看）

```
S1 坐标系与数据 → S2 静态渲染 → S3 能拖 → S4 能存能读 → S5 能播 → 毕业 🎓
```

每级都是一个可运行、可验收的状态。**卡住时退回上一级确认它还是好的**——这是复杂功能的通用开发法。

---

## S1 · 坐标系：像素 ⇄ 秒（本章的数学课，就这一节）

时间轴的本质：**横坐标就是时间**。定一个换算比例，一切迎刃而解：

```javascript
// js/timeline.js
export const PX_PER_SECOND = 20;             // 1 秒 = 20 像素（全文件唯一魔法数字）

export const secToPx = (sec) => sec * PX_PER_SECOND;   // export：scheduler.js 也要用
export const pxToSec = (px) => px / PX_PER_SECOND;
```

前端的工作数据结构（和 21 章 clips 表一一对应）：

```javascript
let clips = [
    // { id, audio_id, filename, display_name, start_seconds, duration }
];
```

一个块的渲染规则由此确定：`left = secToPx(start_seconds)`，`width = secToPx(duration)`。
**先在纸上画一遍**：一条 10 秒的素材从第 4 秒开始 → 左偏 80px、宽 200px。能手算，就懂了。

---

## S2 · 静态渲染：数据 → 画面（先别碰拖拽！）

```html
<div class="timeline" id="timeline">
    <div class="timeline__ruler" id="ruler"></div>     <!-- 刻度尺 -->
    <div class="timeline__track" id="track">           <!-- 轨道：块的容器 -->
        <div class="timeline__playhead" id="playhead"></div>
    </div>
</div>
<button id="save-btn">保存</button>
<button id="play-timeline-btn">▶ 播放时间轴</button>
```

```css
.timeline__track {
    position: relative;              /* ★ 块用绝对定位，容器必须 relative */
    height: 64px;
    background: var(--color-surface);
    border-radius: var(--radius-md);
    overflow-x: auto;
}
.clip {
    position: absolute;
    top: 8px; height: 48px;
    background: var(--color-accent);
    color: #fff;
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 13px;
    overflow: hidden; white-space: nowrap;
    cursor: grab;
    user-select: none;               /* ★ 拖动时不选中文字 */
}
.clip--dragging { cursor: grabbing; opacity: 0.85; z-index: 10; }
.timeline__playhead {
    position: absolute;
    top: 0; bottom: 0; width: 2px;
    background: var(--color-danger);
    left: 0;
    pointer-events: none;            /* 播放头不挡鼠标 */
}
```

```javascript
const trackEl = document.querySelector("#track");

function renderTimeline() {
    trackEl.querySelectorAll(".clip").forEach((el) => el.remove());  // 清旧（保留播放头）
    for (const clip of clips) {
        const el = document.createElement("div");
        el.className = "clip";
        el.textContent = clip.display_name;
        el.style.left = `${secToPx(clip.start_seconds)}px`;
        el.style.width = `${secToPx(clip.duration)}px`;
        el.dataset.clipId = clip.id;             // DOM ↔ 数据 的对应关系
        attachDrag(el, clip);                    // S3 再实现，先放个空函数
        trackEl.append(el);
    }
}
```

**S2 验收**：手写两三条假数据进 `clips` 数组，块的位置、宽度和你纸上算的一致。
（素材库到时间轴的"添加"先用最简单的方式：素材行加一个「+ 添加到时间轴」按钮，
append 一条 `start_seconds` 排在队尾的 clip 并重渲染——拖拽入轴是进阶题。）

---

## S3 · 拖动：Pointer Events 三事件

拖动的通用模式，一次学会终身受用：

```
pointerdown  记住起点（鼠标位置 + 块的原始 start）
pointermove  位移 = 当前位置 - 起点 → 新 start = 原始 start + pxToSec(位移)
pointerup    收尾（这里顺便做吸附）
```

```javascript
function attachDrag(el, clip) {
    el.addEventListener("pointerdown", (e) => {
        e.preventDefault();
        el.setPointerCapture(e.pointerId);       // ★ 神器：鼠标滑出块外也持续收到 move
        el.classList.add("clip--dragging");

        const startX = e.clientX;                // 按下时的鼠标横坐标
        const origin = clip.start_seconds;       // 按下时块的原始位置

        const onMove = (ev) => {
            const deltaSec = pxToSec(ev.clientX - startX);
            // 边界：不许拖成负数（左边界）；右侧任其生长，轨道会滚动
            clip.start_seconds = Math.max(0, origin + deltaSec);
            el.style.left = `${secToPx(clip.start_seconds)}px`;   // 只动 DOM，不重渲染
        };

        const onUp = () => {
            el.removeEventListener("pointermove", onMove);
            el.removeEventListener("pointerup", onUp);
            el.classList.remove("clip--dragging");
            // 吸附：松手时对齐到 0.5 秒网格（手感立升一档）
            clip.start_seconds = Math.round(clip.start_seconds * 2) / 2;
            el.style.left = `${secToPx(clip.start_seconds)}px`;
            markDirty();                          // 有未保存修改（S4 的 UX）
        };

        el.addEventListener("pointermove", onMove);
        el.addEventListener("pointerup", onUp);
    });
}
```

三个关键点：

1. **`setPointerCapture`**：没有它，鼠标一移出块的范围拖动就断——这一行是拖拽体验的分水岭
2. **拖动中只改这一个块的 DOM**，不调 renderTimeline()——整体重绘会闪烁（16 章"全量重绘"
   模式在高频交互下的边界，就在这里显现）
3. **数据是唯一真相**：位置永远先改 `clip.start_seconds`，再由它驱动 DOM——
   和 22 章"UI 是状态的影子"同一哲学

**S3 验收**：块拖起来跟手、出界回弹到 0、松手吸附到半秒、连拖多次位置都对。

---

## S4 · 保存与加载

### 后端（整体替换策略）

编排数据的保存用最稳妥的策略：**全删 + 全插，包在一个事务里**（05 章事务的实战）——
比逐条 diff 简单十倍，数据量小时完全够用：

```python
# routers/timeline.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.database import get_db

router = APIRouter(prefix="/timeline", tags=["timeline"])

class ClipIn(BaseModel):
    audio_id: int
    track: int = 0
    start_seconds: float
    duration: float

@router.get("")
def get_timeline(db=Depends(get_db)):
    rows = db.execute("""
        SELECT clips.*, audios.filename, audios.display_name
        FROM clips JOIN audios ON clips.audio_id = audios.id
        ORDER BY clips.start_seconds
    """).fetchall()                              # ← 21 章补课的 JOIN，此刻兑现
    return [dict(r) for r in rows]

@router.put("")
def save_timeline(clips: list[ClipIn], db=Depends(get_db)):
    try:
        db.execute("DELETE FROM clips")
        db.executemany(
            """INSERT INTO clips (audio_id, track, start_seconds, duration)
               VALUES (?, ?, ?, ?)""",
            [(c.audio_id, c.track, c.start_seconds, c.duration) for c in clips],
        )
        db.commit()                              # 全删全插同生共死
    except Exception:
        db.rollback()                            # 任何一步失败 → 原样回滚
        raise
    return {"saved": len(clips)}
```

### 前端

```javascript
const saveBtn = document.querySelector("#save-btn");

function markDirty() {                            // UX：让"没保存"可见
    saveBtn.textContent = "保存 *";
    saveBtn.classList.add("btn--attention");
}

saveBtn.addEventListener("click", async () => {
    const payload = clips.map(({ audio_id, track, start_seconds, duration }) =>
        ({ audio_id, track, start_seconds, duration }));
    const res = await fetch("http://127.0.0.1:8000/timeline", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (res.ok) {
        saveBtn.textContent = "已保存 ✓";
        saveBtn.classList.remove("btn--attention");
    }
});

async function loadTimeline() {                   // 页面打开时调用
    clips = await (await fetch("http://127.0.0.1:8000/timeline")).json();
    renderTimeline();
}
loadTimeline();
```

**S4 验收**：拖几下 → 保存 → **刷新页面** → 布局分毫不差地回来了。这一刻，
数据库、后端、前端三层真正咬合。

---

## S5 · 播放整条时间轴：调度器

不用 Web Audio，一个"主时钟 + 定时检查"的调度器就能串播（够 AudioBook 用很久）：

```javascript
// js/scheduler.js
import { secToPx } from "./timeline.js";     // 18 章的模块化：换算函数全项目只有一份

const playheadEl = document.querySelector("#playhead");
let playing = false;

export function playTimeline(clips) {
    if (playing || clips.length === 0) return;
    playing = true;

    // 每个块配一个 Audio 对象，提前建好（预加载）
    const items = clips.map((c) => ({
        clip: c,
        audio: new Audio(`http://127.0.0.1:8000/files/${c.filename}`),
        started: false,
    }));

    const total = Math.max(...clips.map((c) => c.start_seconds + c.duration));
    const startAt = performance.now();            // 主时钟起点（毫秒，高精度）

    const timer = setInterval(() => {
        const now = (performance.now() - startAt) / 1000;   // 当前播放到第几秒

        playheadEl.style.left = `${secToPx(now)}px`;        // 播放头随主时钟移动

        for (const item of items) {
            // 到点了且还没播 → 启动
            if (!item.started && now >= item.clip.start_seconds) {
                item.started = true;
                item.audio.play().catch(() => {});
            }
            // 超过块的结尾 → 停止（素材比块长时裁掉尾巴）
            const end = item.clip.start_seconds + item.clip.duration;
            if (item.started && now >= end && !item.audio.paused) {
                item.audio.pause();
            }
        }

        if (now >= total) {                        // 全部播完，收工复位
            clearInterval(timer);
            items.forEach((i) => i.audio.pause());
            playheadEl.style.left = "0px";
            playing = false;
        }
    }, 50);                                        // 每 50ms 检查一次，精度足够
}
```

```javascript
// 这段绑定写在 timeline.js 里（clips 数组住在那个模块）：
import { playTimeline } from "./scheduler.js";

document.querySelector("#play-timeline-btn")
    .addEventListener("click", () => playTimeline(clips));
```

> **诚实说明**：这个调度器的精度约 ±50ms——对"有声书/播客式"的顺序编排绰绰有余，
> 但做不到"两轨音乐严丝合缝地混音"。需要采样级精度时才请出 Web Audio API 的
> `AudioBufferSourceNode.start(time)`——那是进阶路线第一站，地基（数据结构、坐标系、
> 调度思想）你已经全有了，换引擎即可。

**S5 验收**：两段素材一前一后 → 点播放 → 按顺序响起、播放头匀速划过、到点停止、复位。

---

## 毕业验收（用户故事走一遍）

- [ ] 输入文字合成一段 AI 语音（24 章）
- [ ] 录一段自己的开场白（23 章）
- [ ] 两段素材都拖上时间轴，开场白在前，AI 故事在后
- [ ] 保存 → 关掉浏览器重开 → 编排还在
- [ ] 点播放，完整听完你的第一个"作品" 🎓

## 进阶方向（毕业后的路）

| 方向 | 关键词 | 难度 |
|---|---|---|
| 块的裁剪（拖块的边缘改 duration）| 同一套 pointer 模式，判断按在边缘还是中间 | ★★ |
| 多轨道 | track 字段已备好；纵向也算坐标 | ★★ |
| 从素材库直接拖入时间轴 | HTML5 Drag&Drop 或 pointer 跨容器 | ★★★ |
| 采样级混音 / 音量包络 | Web Audio API | ★★★★ |
| 导出成品 mp3 | 服务器端 pydub/ffmpeg 按 clips 拼接 | ★★★ |

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 块的位置全挤在左上角 | 容器没 `position: relative` | 补上（本章 CSS 第一行注释）|
| 拖快了就"脱手" | 没 setPointerCapture | 补上 |
| 拖动时选中了一片文字 | 没禁用选择 | `user-select: none` + pointerdown 里 preventDefault |
| 松手位置和看到的差一点 | 忘了吸附后同步 DOM | onUp 里吸附后再设一次 left |
| 保存后刷新少了块 | PUT 的 payload 字段名和 Pydantic 模型不一致 | 422 响应里看 detail |
| 播放时全部同时响 | 主时钟没用 / started 标记漏了 | 对照 S5 调度器逐行核对 |
| 播放头不动 | playhead 被重渲染删掉了 | renderTimeline 只删 .clip，别动播放头 |
| 第二次播放没声音 | playing 标记没复位 / Audio 对象复用报错 | 播完复位 playing；每次播放新建 items |

---

> 🎓 走到这里，你已经独立完成了一个包含 AI 能力、文件系统、数据库、复杂前端交互的完整产品。
> 回头看看 01 章的那个 venv 命令——这条路是你自己一步步走完的。
> 接下来：把它变成你真正的 AudioBook，然后迭代、部署（11 章）、给别人用。造物开始了。
