# 23 · 素材入库：上传与录音

> 交付里程碑 M3：用户可以**上传音频文件**或**直接对着麦克风录一段**，素材出现在列表里，可播放可删除。
> 预计学习时间：4~5 小时。前置：22 章（播放器要能播它们）、16 章（fetch）。

---

## 学习目标

1. 前端：文件选择、**拖拽上传**、上传中的状态反馈（UX）
2. 后端：`UploadFile` 接收、**uuid 安全重命名**、类型/大小校验、mutagen 读时长、入库
3. 前端录音：麦克风授权（UX）→ MediaRecorder → 复用上传通道
4. 素材库列表：展示、试听、删除（文件和记录一起删）

---

## 1. 上传的完整链路（先看地图）

```
用户选文件/录音 ──▶ FormData ──fetch POST──▶ UploadFile 接收
                                              │ 校验类型和大小
                                              │ uuid 重命名存入 uploads/
                                              │ mutagen 读时长
                                              ▼
前端刷新素材列表 ◀──返回新记录 JSON──  INSERT 进 audios 表
```

和 16 章 Todo 的 POST 唯一的区别：**发的不是 JSON，是文件**——载体从 `JSON.stringify` 换成 `FormData`。

---

## 2. 后端：接收文件的完整实现

```python
# routers/audios.py
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from mutagen import File as MutagenFile

from app.core.config import settings
from app.db.database import get_db

router = APIRouter(prefix="/audios", tags=["audios"])

UPLOAD_DIR = Path("uploads")
ALLOWED_TYPES = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/webm", "audio/mp4"}
MAX_SIZE = 50 * 1024 * 1024      # 50MB（放进 08 章的 Settings 更好）

@router.post("", status_code=201)
async def upload_audio(file: UploadFile, db=Depends(get_db)):
    # ── 校验① 类型：先看 content_type（能挡住误操作，挡不住恶意——见下方要点）
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, f"unsupported type: {file.content_type}")

    # ── 校验② 大小：边读边数，超限即停（不要信任 Content-Length 头）
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(413, "file too large (max 50MB)")

    # ── 关键安全动作：uuid 重命名，只保留原始扩展名 ──
    ext = Path(file.filename or "audio.mp3").suffix.lower() or ".mp3"
    stored_name = f"{uuid.uuid4().hex}{ext}"       # 例：3f2a9c...b1.mp3
    dest = UPLOAD_DIR / stored_name
    dest.write_bytes(data)

    # ── mutagen 读时长（顺带验证它真的是音频）──
    meta = MutagenFile(dest)
    if meta is None or meta.info is None:
        dest.unlink()                              # 假音频：删文件、拒绝
        raise HTTPException(415, "not a valid audio file")
    duration = round(meta.info.length, 2)

    # ── 入库（21 章的 audios 表）──
    cursor = db.execute(
        """INSERT INTO audios (filename, display_name, duration, size_bytes, source)
           VALUES (?, ?, ?, ?, 'upload')""",
        (stored_name, file.filename or stored_name, duration, len(data)),
    )
    db.commit()
    row = db.execute("SELECT * FROM audios WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)
```

### 为什么必须 uuid 重命名？（安全课）

用户上传的文件名是**不可信输入**（04/05 章"参数化查询"同款思想）：

- `../../etc/passwd` 这样的名字可以**路径穿越**，写到你意想不到的位置
- `报告 final(1).mp3` 含空格/中文/特殊字符，URL 编码问题成堆
- 两个用户都传 `voice.mp3` → 互相覆盖

**uuid 做磁盘文件名（系统用），原始名存 `display_name`（给人看）**——两个需求各自满足。

> **要点**：`content_type` 是浏览器报的，可以伪造——所以还要 mutagen 真解析一次做二次验证。
> "前端校验管体验，后端校验管安全"（13 章讲过），文件上传是这条原则最典型的战场。

素材列表与删除（CRUD 复习，快速带过）：

```python
@router.get("")
def list_audios(db=Depends(get_db)):
    rows = db.execute("SELECT * FROM audios ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

@router.delete("/{audio_id}", status_code=204)
def delete_audio(audio_id: int, db=Depends(get_db)):
    row = db.execute("SELECT * FROM audios WHERE id = ?", (audio_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "audio not found")
    (UPLOAD_DIR / row["filename"]).unlink(missing_ok=True)   # 文件和记录一起删
    db.execute("DELETE FROM audios WHERE id = ?", (audio_id,))
    db.commit()
```

（被时间轴引用的素材，外键会拦住删除——这正是 21 章打开 `PRAGMA foreign_keys` 的价值。
把 409 错误提示给用户："该素材正在时间轴中使用"。）

---

## 3. 前端：选择、拖拽、上传反馈

```html
<div id="drop-zone" class="drop-zone">
    <p>拖拽音频到这里，或
        <label class="link">点击选择<input id="file-input" type="file"
               accept="audio/*" hidden></label>
    </p>
    <p id="upload-status" class="muted"></p>
</div>
```

```javascript
// js/upload.js
import { refreshLibrary } from "./library.js";

const dropZone = document.querySelector("#drop-zone");
const fileInput = document.querySelector("#file-input");
const statusEl = document.querySelector("#upload-status");

async function uploadFile(file) {
    // ── UX：前端预检，让用户不用等一次网络往返才知道错 ──
    if (!file.type.startsWith("audio/")) {
        statusEl.textContent = "只支持音频文件";
        return;
    }
    if (file.size > 50 * 1024 * 1024) {
        statusEl.textContent = "文件超过 50MB 上限";
        return;
    }

    // ── UX：上传中状态（禁用重复操作 + 明确反馈）──
    statusEl.textContent = `正在上传 ${file.name}…`;
    dropZone.classList.add("drop-zone--busy");

    try {
        const formData = new FormData();
        formData.append("file", file);              // 键名必须和后端参数名一致！

        const res = await fetch("http://127.0.0.1:8000/audios", {
            method: "POST",
            body: formData,       // ★ 不要手动设置 Content-Type！浏览器会自动带 boundary
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        statusEl.textContent = "上传成功 ✓";
        await refreshLibrary();                     // 素材列表刷新
    } catch (err) {
        statusEl.textContent = `上传失败：${err.message}`;
    } finally {
        dropZone.classList.remove("drop-zone--busy");
    }
}

// 方式一：点击选择
fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) uploadFile(fileInput.files[0]);
    fileInput.value = "";                           // 允许连续选同一个文件
});

// 方式二：拖拽（三个事件，缺一不可）
dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();                             // ★ 不阻止默认，drop 永远不触发
    dropZone.classList.add("drop-zone--over");      // 视觉反馈：拖到位了
});
dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drop-zone--over");
});
dropZone.addEventListener("drop", (e) => {
    e.preventDefault();                             // ★ 阻止浏览器直接打开文件
    dropZone.classList.remove("drop-zone--over");
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
});
```

三个必记的坑都标了 ★：FormData 的键名对齐、**不能手动设 Content-Type**（会破坏
multipart 的 boundary，后端收到 422）、dragover 必须 preventDefault。

---

## 4. 录音：MediaRecorder 三步曲

录音的美妙之处：录完得到一个 Blob，**包装成 File 就能复用上面的整条上传链路**——零后端改动。

```html
<button id="record-btn">🎙 开始录音</button>
<span id="record-time" class="muted"></span>
```

```javascript
// js/recorder.js
import { uploadFile } from "./upload.js";     // 复用！（把 uploadFile 加上 export）

const recordBtn = document.querySelector("#record-btn");
const timeEl = document.querySelector("#record-time");

let recorder = null;
let chunks = [];
let timer = null;

recordBtn.addEventListener("click", async () => {
    // ── 正在录 → 停止 ──
    if (recorder && recorder.state === "recording") {
        recorder.stop();
        return;
    }

    // ── 第 1 步：请求麦克风（浏览器会弹授权框）──
    let stream;
    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
        // UX：被拒绝是常态，给出路而不是甩错误
        alert("需要麦克风权限才能录音。请在浏览器地址栏左侧的设置里允许。");
        return;
    }

    // ── 第 2 步：开录，分片攒数据 ──
    chunks = [];
    recorder = new MediaRecorder(stream);           // 浏览器默认录成 webm/opus
    recorder.addEventListener("dataavailable", (e) => chunks.push(e.data));

    // ── 第 3 步：停止时打包上传 ──
    recorder.addEventListener("stop", () => {
        stream.getTracks().forEach((t) => t.stop());   // ★ 释放麦克风（关掉红点）
        clearInterval(timer);
        const blob = new Blob(chunks, { type: "audio/webm" });
        const file = new File([blob], `录音 ${new Date().toLocaleString()}.webm`,
                              { type: "audio/webm" });
        uploadFile(file);                              // 走 23.3 的同一条路！
        recordBtn.textContent = "🎙 开始录音";
    });

    recorder.start();
    recordBtn.textContent = "⏹ 停止录音";

    // UX：录音计时（用户必须知道"正在录"以及录了多久）
    const startAt = Date.now();
    timer = setInterval(() => {
        const s = Math.floor((Date.now() - startAt) / 1000);
        timeEl.textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
    }, 500);
});
```

三处 UX 决策值得注意：**授权被拒给出路**（告诉用户去哪开权限）、**录音中有计时**
（无反馈的录音按钮是最吓人的 UI）、**停止后立刻释放麦克风**（浏览器标签上的红点消失，
用户才确信"没在偷听"——信任感设计）。

> **要点**：浏览器录音的原生格式是 **webm**（21 章格式表提过），`<audio>` 能直接播它，
> 上传链路也照收——不需要转码。将来若需要统一成 mp3，才是 pydub/ffmpeg 出场的时候。

---

## 5. 素材库列表（把一切串起来）

```javascript
// js/library.js
import { loadAndPlay } from "./player.js";      // 22 章的播放器

const listEl = document.querySelector("#library");

export async function refreshLibrary() {
    const res = await fetch("http://127.0.0.1:8000/audios");
    const audios = await res.json();

    listEl.innerHTML = "";
    for (const a of audios) {
        const li = document.createElement("li");
        li.className = "audio-row";

        const icon = { upload: "📁", record: "🎙", ai: "🤖" }[a.source] || "🎵";
        const name = document.createElement("span");
        name.className = "audio-row__name";
        name.textContent = `${icon} ${a.display_name}`;

        const dur = document.createElement("span");
        dur.className = "muted";
        dur.textContent = formatTime(a.duration);   // 22 章的函数，抽到公共模块

        const playBtn = document.createElement("button");
        playBtn.textContent = "试听";
        playBtn.addEventListener("click", () =>
            loadAndPlay(`http://127.0.0.1:8000/files/${a.filename}`));

        const delBtn = document.createElement("button");
        delBtn.textContent = "删除";
        delBtn.addEventListener("click", async () => {
            if (!confirm(`删除「${a.display_name}」？`)) return;   // 不可逆操作必须确认
            const res = await fetch(`http://127.0.0.1:8000/audios/${a.id}`,
                                    { method: "DELETE" });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                alert(err.detail || "删除失败（可能正被时间轴使用）");
                return;
            }
            await refreshLibrary();
        });

        li.append(name, dur, playBtn, delBtn);
        listEl.append(li);
    }
}

refreshLibrary();
```

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 上传收到 422 | 手动设了 Content-Type / FormData 键名和后端参数不一致 | 删掉手动头；键名 = 参数名 `file` |
| `Form data requires "python-multipart"` | 依赖没装 | `pip install python-multipart`（06 章预告过）|
| drop 事件不触发 | dragover 没 preventDefault | 补上 |
| 拖文件进去浏览器直接打开了它 | drop 没 preventDefault | 补上 |
| 录音权限弹框不出现 | 非安全上下文 | localhost 可以；局域网 IP 访问需 https（getUserMedia 的硬性要求）|
| 录完麦克风红点不消失 | 没停 tracks | `stream.getTracks().forEach(t => t.stop())` |
| mutagen 读不出时长 | 文件真不是音频 / webm 某些编码 | 按代码删文件拒绝；webm 读不出时长可回退存 0，前端播放时用 loadedmetadata 修正 |
| 同一文件第二次选不触发 change | input 值没清 | `fileInput.value = ""` |

---

## 小练习（交付 M3）

1. 完整实现上传链路，验收：传一个 mp3 → 列表出现（名字、时长正确）→ 试听 → 删除后 uploads/ 里文件也消失。
2. 故意上传一个改了扩展名的 txt 文件，验证 mutagen 二次校验把它拦下且没留垃圾文件。
3. 实现录音，验收：授权 → 计时跳动 → 停止 → 素材库出现 🎙 记录 → 能试听。
   然后在浏览器设置里**主动拒绝**麦克风权限，验证你的引导提示。
4. 在时间轴功能还没做之前，先手动往 clips 表 INSERT 一条引用某素材的记录，
   再试着删除该素材——验证外键保护和你的 409 提示。
5. （UX 审视）对照你的素材库：每个操作都有反馈吗？上传中能看出"正在忙"吗？
   删除有确认吗？——这三问以后带给你做的每个界面。

> 下一章：[24 · AI 语音合成](24-ai-voice-synthesis.md) —— 让文字变成素材库里的声音。
