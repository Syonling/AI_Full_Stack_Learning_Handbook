# 22 · 音频播放：从 `<audio>` 到自定义播放器

> 交付里程碑 M2：网页上有一个漂亮好用的播放器——能播、能暂停、能拖进度、能调倍速、显示波形。
> 预计学习时间：3~4 小时。前置：21 章骨架已就位，15 章（DOM/事件）扎实。

---

## 学习目标

1. 后端用 `StaticFiles` 提供音频，并理解**拖进度条为什么依赖 Range 请求**
2. 掌握 `<audio>` 的 JS 控制面：属性、方法、事件
3. 正确处理**浏览器自动播放拦截**（音频应用第一 UX 坑）
4. 亲手做一个自定义播放器（进度条 / 时间显示 / 倍速）
5. 用 wavesurfer.js 加上波形

---

## 1. 后端：两行代码提供音频

在 main.py 里把 uploads/ 挂载出去（06 章学过 StaticFiles，这次真正派上用场）：

```python
from fastapi.staticfiles import StaticFiles

app.mount("/files", StaticFiles(directory="uploads"), name="files")
# uploads/abc123.mp3  →  可通过 http://127.0.0.1:8000/files/abc123.mp3 访问
```

### 为什么必须用它：Range 请求（拖进度条的幕后英雄）

用户把进度条拖到第 3 分钟时，浏览器**不会**下载整个文件再跳转，而是发一个带
`Range: bytes=2880000-` 头的请求："从这个字节开始给我"。服务器返回 **206 Partial Content**。

- `StaticFiles` **自动支持** Range —— 这就是选它的原因
- 如果你自己写路由返回整个文件、不处理 Range：进度条拖不动、seek 卡死、移动端问题成堆

验证一下（curl 技能，10 章）：

```bash
# 先手动放一个 test.mp3 到 uploads/ 里
curl -s -i -H "Range: bytes=0-99" http://127.0.0.1:8000/files/test.mp3 | head -5
# 看到 HTTP/1.1 206 Partial Content 就对了
```

---

## 2. 起步：一行 HTML 就是播放器

```html
<audio src="http://127.0.0.1:8000/files/test.mp3" controls></audio>
```

`controls` 给你浏览器原生的播放器 UI——功能全但长相不可控、各浏览器不一致。
**开发原则：先用 `controls` 验证链路通，再换自定义 UI。**

---

## 3. `<audio>` 的 JS 控制面（自定义播放器的全部原料）

```javascript
const audio = new Audio("http://127.0.0.1:8000/files/test.mp3");
// 或控制页面上已有的：const audio = document.querySelector("audio");

// ── 方法与属性 ──
audio.play();                  // 开始播放（注意：返回 Promise，见第 4 节）
audio.pause();
audio.currentTime = 42.5;      // 跳到第 42.5 秒（seek，就这一行！）
audio.duration;                // 总时长（秒）——元数据加载完才有值
audio.playbackRate = 1.5;      // 倍速
audio.volume = 0.8;            // 音量 0~1
audio.paused;                  // 是否处于暂停态（布尔）

// ── 关键事件 ──
audio.addEventListener("loadedmetadata", () => {
    console.log("时长可用了:", audio.duration);   // 初始化 UI 用它
});
audio.addEventListener("timeupdate", () => {
    console.log("播放到:", audio.currentTime);    // 每秒触发约 4 次，驱动进度条
});
audio.addEventListener("ended", () => {
    console.log("播完了");                        // 切下一首/复位按钮用它
});
audio.addEventListener("error", () => {
    console.log("加载失败", audio.error);
});
```

> **要点**：`duration` 在 `loadedmetadata` 事件之前是 `NaN`——
> 所有"显示总时长"的代码必须写在这个事件回调里，这是本章第一坑。

---

## 4. UX 第一坑：自动播放拦截

所有现代浏览器都禁止**没有用户交互就出声**（否则网页广告会吵翻天）。规则：

- 页面一加载就 `audio.play()` → **被拒绝**，控制台报 `NotAllowedError`
- 用户点过页面上任何东西之后 → play() 正常

正确姿势两条：

```javascript
// ① 播放永远由用户手势触发（点击播放按钮），别自作主张自动播
playBtn.addEventListener("click", () => audio.play());

// ② play() 返回 Promise，养成接住失败的习惯
async function safePlay() {
    try {
        await audio.play();
    } catch (err) {
        // 被策略拦截或文件有问题——把状态还原成"未播放"，提示用户点击播放
        showHint("点击 ▶ 开始播放");
    }
}
```

> **产品视角**：这不是限制，是设计指引——**声音永远应该是用户"请求"来的**。
> AudioBook 的所有播放入口都做成明确的按钮，不做任何自动播放。

---

## 5. 实战：自定义播放器

三个文件各就各位（18 章的组织方式）。功能：播放/暂停、可拖进度条、时间显示、倍速。

**HTML（结构）**

```html
<div class="player" id="player">
    <button id="play-btn" class="player__btn">▶</button>
    <span id="time-now">0:00</span>
    <input id="seek" class="player__seek" type="range" min="0" max="100" step="0.1" value="0">
    <span id="time-total">0:00</span>
    <select id="rate">
        <option value="1" selected>1×</option>
        <option value="1.25">1.25×</option>
        <option value="1.5">1.5×</option>
        <option value="2">2×</option>
    </select>
</div>
```

**JS（行为）—— js/player.js**

```javascript
const audio = new Audio();          // 不带 src，播放什么由外部指定
const playBtn = document.querySelector("#play-btn");
const seekEl = document.querySelector("#seek");
const timeNowEl = document.querySelector("#time-now");
const timeTotalEl = document.querySelector("#time-total");
const rateEl = document.querySelector("#rate");

// 秒 → "m:ss"（handbook 值得收藏的小函数）
function formatTime(seconds) {
    if (!Number.isFinite(seconds)) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
}

// 对外的唯一入口：播放某个素材（23 章的素材列表会调用它）
export function loadAndPlay(url) {
    audio.src = url;
    audio.play().catch(() => { playBtn.textContent = "▶"; });
}

// ── 播放/暂停按钮：图标跟随真实状态 ──
playBtn.addEventListener("click", () => {
    if (audio.paused) audio.play().catch(() => {});
    else audio.pause();
});
audio.addEventListener("play",  () => { playBtn.textContent = "⏸"; });
audio.addEventListener("pause", () => { playBtn.textContent = "▶"; });

// ── 元数据就绪：初始化总时长和进度条量程 ──
audio.addEventListener("loadedmetadata", () => {
    seekEl.max = audio.duration;
    timeTotalEl.textContent = formatTime(audio.duration);
});

// ── 播放中：驱动进度条与时间（单向：audio → UI）──
let seeking = false;                 // 用户正在拖动时，暂停 UI 跟随
audio.addEventListener("timeupdate", () => {
    if (seeking) return;
    seekEl.value = audio.currentTime;
    timeNowEl.textContent = formatTime(audio.currentTime);
});

// ── 拖动进度条：按下时只预览，松手才真正 seek（顺滑的关键）──
seekEl.addEventListener("input", () => {          // 拖动过程持续触发
    seeking = true;
    timeNowEl.textContent = formatTime(Number(seekEl.value));
});
seekEl.addEventListener("change", () => {         // 松手触发一次
    audio.currentTime = Number(seekEl.value);     // ← 触发 Range 请求的时刻
    seeking = false;
});

// ── 倍速 ──
rateEl.addEventListener("change", () => {
    audio.playbackRate = Number(rateEl.value);
});

audio.addEventListener("ended", () => { playBtn.textContent = "▶"; });
```

**CSS 要点**（完整样式自己按 19 章 Apple 风发挥）：

```css
.player { display: flex; align-items: center; gap: var(--space-1); }
.player__seek { flex: 1; accent-color: var(--color-accent); }  /* range 原生上色 */
```

这段代码浓缩了播放器 UI 的**通用模式**，值得体会：

1. **UI 是状态的影子**：按钮图标由 `play`/`pause` 事件驱动，而不是点击时自己切——
   这样无论谁触发的播放（快捷键、代码、别的按钮），图标永远正确
2. **拖动三件套**：`input` 预览 + `change` 提交 + `seeking` 锁——没有这把锁，
   拖动时 `timeupdate` 会不停把滑块拽回去，手感极差（本章第二坑）

---

## 6. 波形显示：wavesurfer.js

波形让"声音"变得**可见**——用户一眼看出静音段、高潮段在哪。CDN 引入即用：

```html
<script src="https://unpkg.com/wavesurfer.js@7"></script>
<div id="waveform"></div>

<script>
const wavesurfer = WaveSurfer.create({
    container: "#waveform",
    url: "http://127.0.0.1:8000/files/test.mp3",
    height: 64,
    waveColor: "#c7c7cc",          // 未播部分：浅灰（19 章的克制配色）
    progressColor: "#0071e3",      // 已播部分：强调色
    cursorColor: "transparent",
});

wavesurfer.on("interaction", () => wavesurfer.play());   // 点击波形任意处播放
</script>
```

注意：wavesurfer **自带播放能力**（它内部也管理一个音频源）。所以二选一：
要么"第 5 节自定义播放器"，要么"wavesurfer 全家桶"（它也有进度/事件 API），
**别让两个 audio 同时放**。AudioBook 建议：素材预览用 wavesurfer，
时间轴播放用第 5 节的 Audio 对象（25 章会看到为什么）。

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `NotAllowedError: play() failed` | 无用户手势自动播放 | 播放必须由点击触发；catch 住并引导 |
| 总时长显示 NaN | duration 读早了 | 放进 `loadedmetadata` 回调 |
| 进度条拖不动 / 拖了弹回 | 后端不支持 Range | 用 StaticFiles 挂载；自查 curl 是否返回 206 |
| 拖动时滑块疯狂抖动 | timeupdate 和拖动打架 | 第 5 节的 `seeking` 锁 |
| 换 src 后播放报错 | 旧的播放 Promise 未处理 | play() 永远 `.catch()`；换源前先 `pause()` |
| 两个声音叠着响 | wavesurfer 和 Audio 各播各的 | 二选一，或播放前互相 pause |
| CORS 报错 | 前端 file:// 打开 + 挂载路径拼错 | 检查 URL；demo 式 CORS 配置（06 章）|

---

## 小练习（交付 M2）

1. 手动放一个 mp3 进 uploads/，用 curl 验证 206，然后 `<audio controls>` 一行版跑通链路。
2. 完成第 5 节自定义播放器，逐项验收：拖进度顺滑不抖、时间显示正确、倍速生效、
   播完图标复位。
3. 故意在页面加载时调用 `audio.play()`，观察 NotAllowedError，然后按第 4 节改正。
4. 加上 wavesurfer 波形，配色换成你 19 章主题的令牌色。
5. （思考题）为什么"按钮图标跟随 play/pause 事件"比"点击时切换图标"更健壮？
   想一个后者会出错的场景。

> 下一章：[23 · 素材入库：上传与录音](23-audio-upload-recording.md) —— 让用户的声音进入系统。
