# 21 · 音频应用总览：架构与技术选型

> 「项目实践」开篇。从这章起，我们把前 20 章的能力组装成一个真实产品：
> **AudioBook 音频工作台**——上传/录音/AI 合成音频素材，管理它们，最终在时间轴上编排成作品。
> 本章不写多少代码，但做出的每个决策都决定后面四章怎么走。预计学习时间：2~3 小时。
> 前置：后端主线（04~07）+ 前端 13~16 + **18 章**（本项目前端用模块化写法组织，需要 18 章的
> ES Modules 和本地服务器知识）。完全没接触过音频？正好，第 1 节就是为你写的。

---

## 学习目标

1. 用 20 分钟建立**数字音频的最小知识地图**（采样率、格式、大小估算）
2. 看懂整个项目的**架构图**和五章路线
3. 理解音频应用的第一决策：**文件存磁盘，数据库只存元数据**
4. 设计出两张核心表，顺便补上 **外键与 JOIN**（05 章没讲的）
5. 拿到一张"什么场景用什么工具"的选型总表

---

## 1. 音频零基础速成（20 分钟够用版）

不需要懂声学，只需要这几个概念——它们会在后面四章反复出现：

**声音怎么变成文件？** 三步：

```
真实声波 ──采样──▶ 每秒测量 N 次 ──量化──▶ 每次测量记成数字 ──编码──▶ 文件
           (采样率)                (位深)                    (格式)
```

| 概念 | 是什么 | 你只需记住 |
|---|---|---|
| **采样率** | 每秒测量声波多少次，单位 Hz | 44100 Hz（CD 质量）是通用默认，人声 24000 也够 |
| **比特率** | 每秒数据量，单位 kbps | mp3 常见 128/192 kbps，越高越清晰文件越大 |
| **声道** | 单声道 mono / 立体声 stereo | 人声/有声书用 mono 省一半空间 |

**格式怎么选？**（Web 场景三选一）

| 格式 | 特点 | 什么时候用 |
|---|---|---|
| **mp3** | 有损压缩，所有浏览器都支持 | ✅ **默认选它**，兼容性之王 |
| wav | 无损、巨大（1 分钟 ≈ 10MB） | 需要后期精细处理的原始素材 |
| webm/ogg | 浏览器录音的原生产物 | MediaRecorder 录出来就是它（23 章会遇到）|

**文件多大？** 心算公式：`大小 ≈ 比特率(kbps) ÷ 8 × 秒数`。
128kbps 的 mp3：1 分钟 ≈ 1MB —— 这个数量级感觉会帮你做后面所有的限制和 UX 决策。

> **要点**：本项目全程"拿来就用"现成音频文件，**不需要任何声学/信号处理知识**。
> 上面这张表就是全部理论行囊。

---

## 2. 项目蓝图：AudioBook 音频工作台

给你的 Audio Book 项目一个完整的产品形态，四个功能区、四个章节交付：

```
┌────────────────────────────────────────────────┐
│  AudioBook 工作台                                │
│                                                 │
│  ① 素材库（23 章）      ② 播放器（22 章）          │
│     上传 / 录音            波形、进度条、倍速       │
│                                                 │
│  ③ AI 合成（24 章）     ④ 时间轴（25 章·压轴）     │
│     文字 → 语音素材        拖块编排、保存、串播      │
└────────────────────────────────────────────────┘
```

用户故事（也是最终验收标准）：

> 用户输入一段故事文字 → AI 合成为语音，出现在素材库；用户再录一段自己的开场白上传；
> 然后把两段音频拖到时间轴上排好顺序，点保存；下次打开，作品还在，点播放完整听完。

---

## 3. 架构图：三层各干什么

```
浏览器（前端）
│  <audio> 播放器 · 上传/录音 UI · 时间轴拖拽
│
│         HTTP（fetch / FormData / JSON）
▼
FastAPI（后端）
│  /audios  上传·列表·删除     /synthesize  AI 合成
│  /timeline  保存·读取        /files/*  静态提供音频（支持拖进度条）
│
├──────────────► uploads/ 文件夹     ← 音频文件本体（磁盘）
▼
SQLite
   audios 表（素材元数据）· clips 表（时间轴编排数据）
```

和 demo 的 Todo 相比，只多了一个新角色：**磁盘上的 uploads/ 文件夹**。这引出第一决策——

---

## 4. 第一决策：文件存磁盘，数据库只存"关于文件的信息"

新手直觉是"音频存进数据库"（SQLite 确实有 BLOB 类型能存二进制）。**不要这么做**：

| | 文件塞数据库（BLOB）| ✅ 文件存磁盘 + 路径入库 |
|---|---|---|
| 数据库体积 | 传 100 个音频就上 GB，备份/迁移噩梦 | 数据库永远只有几百 KB |
| 播放 | 每次播放都要从库里捞大二进制 | StaticFiles 直接高效提供，还免费获得"拖进度条"支持（22 章）|
| 生态 | 违背常规，工具链都不配合 | 业界标准做法，未来换云存储（S3 等）只改路径 |

所以铁律是：**二进制归文件系统，结构化信息归数据库**。数据库里的 `audios` 表存的是"关于这个文件的一切"——文件名、时长、大小、来源——唯独不存声音本身。

---

## 5. 数据库设计（+ 补课：外键与 JOIN）

两张表撑起整个项目：

```sql
-- 素材库：每行 = 一个音频文件的"档案"
CREATE TABLE IF NOT EXISTS audios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,          -- 磁盘上的实际文件名（uuid，23 章讲为什么）
    display_name TEXT NOT NULL,      -- 给用户看的名字（原始文件名/合成标题）
    duration REAL NOT NULL,          -- 时长（秒），mutagen 读取
    size_bytes INTEGER NOT NULL,
    source TEXT NOT NULL,            -- 'upload' | 'record' | 'ai'（三个来源，三章各填一种）
    created_at TEXT DEFAULT (datetime('now'))
);

-- 时间轴：每行 = 时间轴上的一个音频块
CREATE TABLE IF NOT EXISTS clips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_id INTEGER NOT NULL REFERENCES audios(id),   -- ★ 外键
    track INTEGER NOT NULL DEFAULT 0,    -- 第几条轨道（先做单轨，字段留好）
    start_seconds REAL NOT NULL,         -- 块在时间轴上的起点
    duration REAL NOT NULL               -- 块时长（先等于素材时长，将来支持裁剪）
);
```

### 补课①：外键（FOREIGN KEY）

`clips.audio_id REFERENCES audios(id)` 声明"这一列的值必须是 audios 表里真实存在的 id"——
两张表从此产生**关系**：一个素材可以被多个块引用（一对多）。

SQLite 默认不强制检查外键，每个连接要手动打开（加进 05 章学的 `get_db`）：

```python
conn.execute("PRAGMA foreign_keys = ON")   # 之后删除被引用的素材会报错，保护数据一致
```

### 补课②：JOIN（连表查询）

时间轴播放时需要"每个块 + 它对应素材的文件名"，两张表的数据一次查出来：

```sql
SELECT clips.*, audios.filename, audios.display_name
FROM clips
JOIN audios ON clips.audio_id = audios.id    -- 按外键把两张表"拼"起来
ORDER BY clips.start_seconds;
```

读法："取 clips 的每一行，按 `audio_id = id` 的对应关系，把 audios 的列拼在旁边。"
这是 SQL 里除 05 章四大操作外最重要的一招，25 章会实际用到。

---

## 6. 技术选型总表（每一项都答"为什么"）

| 场景 | 选择 | 为什么是它 |
|---|---|---|
| 播放 | 原生 `<audio>` | 内置解码/缓冲/进度，90% 场景够用；Web Audio API 是专业混音才需要的深水区，本项目不下 |
| 波形显示 | wavesurfer.js | 事实标准，CDN 引入即用 |
| 录音 | MediaRecorder API | 浏览器原生，零依赖 |
| 上传接收 | `UploadFile` + python-multipart | FastAPI 官方方案（06 章提过，23 章实战）|
| 读音频元数据 | mutagen | 纯 Python、无系统依赖，读时长/比特率一行搞定 |
| 语音合成 | 适配器模式：开发用 edge-tts，生产换 AI API | 24 章的主题——换供应商只改一个函数 |
| 音频剪辑/转码 | pydub（+ ffmpeg）| **本项目用不到**，列在这里是让你知道需要时找谁；ffmpeg 是系统级依赖，能不引入就不引入 |
| 存储 | 磁盘 uploads/ + SQLite 元数据 | 第 4 节的铁律 |

```bash
# 后端新增依赖（在 07 章项目基础上）
pip install python-multipart mutagen edge-tts
```

---

## 7. 项目骨架与五章路线

### 7.1 目录结构（直接套 20 章的分层模板）

```
audiobook/
├── requirements.txt
├── .env.example
├── uploads/              # 音频文件本体（.gitignore 掉，留 .gitkeep 占位）
├── app/
│   ├── __init__.py
│   ├── main.py           # 组装 + StaticFiles 挂载 + CORS
│   ├── core/config.py    # Settings + 路径常量（↓ 7.2 给出完整版）
│   ├── db/database.py    # ↓ 7.2 给出完整版
│   ├── schemas/          # audio.py / clip.py
│   ├── services/         # tts.py（24 章创建）
│   └── routers/          # audios.py / synthesize.py / timeline.py
└── frontend/
    ├── index.html        # ↓ 7.3 给出完整骨架
    ├── css/              # 18 章分层 + 19 章 Apple 风令牌
    └── js/               # utils.js / api.js / player.js / library.js /
                          # upload.js / recorder.js / synthesize.js /
                          # timeline.js / scheduler.js（各章逐个填充）
```

### 7.2 database.py 完整版（后面四章直接引用，抄这里）

```python
# app/db/database.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "audiobook.db"


def connect() -> sqlite3.Connection:
    """开一个新连接（后台任务等场景自己开自己关，24 章会用到）。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")    # 每个连接都要打开外键检查
    return conn


def get_db():
    """FastAPI 依赖：每个请求一个连接（07 章的老朋友 + 外键开关）。"""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    conn = connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS audios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            display_name TEXT NOT NULL,
            duration REAL NOT NULL,
            size_bytes INTEGER NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ready',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS clips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audio_id INTEGER NOT NULL REFERENCES audios(id),
            track INTEGER NOT NULL DEFAULT 0,
            start_seconds REAL NOT NULL,
            duration REAL NOT NULL
        );
    """)
    conn.commit()
    conn.close()
```

（`status` 列本是 24 章才需要的，建表时一步到位，免得中途 ALTER。）

同样一步到位的还有 **config.py**——把「项目根目录」和「上传目录」定成**绝对路径常量**，
后面所有章节的文件读写都引用它（贯彻 05/07 章"路径用 `__file__` 定位"的教义，
避免"从不同目录启动、文件建到别处"的坑）：

```python
# app/core/config.py
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent    # audiobook/ 根目录
UPLOAD_DIR = BASE_DIR / "uploads"                           # 音频文件目录（绝对路径）


class Settings(BaseSettings):
    app_name: str = "AudioBook"
    log_level: str = "INFO"
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env",
                                      env_file_encoding="utf-8")


settings = Settings()
```

### 7.3 index.html 页面骨架（四个功能区一次搭好，后面各章往里填）

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AudioBook 工作台</title>
    <link rel="stylesheet" href="css/base.css">
    <link rel="stylesheet" href="css/components.css">
    <script src="js/main.js" type="module" defer></script>
</head>
<body>
    <main class="container">
        <h1>AudioBook 工作台</h1>

        <section id="section-synthesize">      <!-- 24 章：AI 合成表单 -->
            <h2>AI 合成</h2>
        </section>

        <section id="section-upload">           <!-- 23 章：上传区 + 录音按钮 -->
            <h2>添加素材</h2>
        </section>

        <section id="section-library">          <!-- 23 章：素材列表 -->
            <h2>素材库</h2>
            <ul id="library"></ul>
        </section>

        <section id="section-player">           <!-- 22 章：播放器 -->
            <h2>试听</h2>
        </section>

        <section id="section-timeline">         <!-- 25 章：时间轴 -->
            <h2>时间轴</h2>
        </section>
    </main>
</body>
</html>
```

每章的 HTML 片段（播放器、drop-zone、时间轴……）就填进对应的 `<section>` 里；
`js/main.js` 作为入口 `import` 各功能模块（18 章的组织方式）。

### 7.4 怎么跑起来（每次开发的固定动作，两个终端）

```bash
# 终端 1：后端（在 audiobook/ 根目录）
source .venv/bin/activate
uvicorn app.main:app --reload          # 包结构启动方式，20 章讲过

# 终端 2：前端（在 audiobook/frontend/ 目录）
python3 -m http.server 3000
# 浏览器访问 http://localhost:3000
```

**为什么前端必须起服务器、不能双击打开？** 因为 js/ 用了 `import/export` 模块化
（18 章讲过 file:// 下会被浏览器拒绝）。

**因此 CORS 必须配置**（前端在 3000，API 在 8000，是跨域）——main.py 里照 06 章加上：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],   # 比 demo 的 "*" 收紧一步
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 7.5 五章里程碑

| 里程碑 | 章节 | 验收标准 |
|---|---|---|
| M1 骨架 + 表 | 本章练习 | 两个终端都能跑起来，空页面五个区块可见，两张表建好 |
| M2 能播 | 22 | 手放一个 mp3 进 uploads，网页上有完整播放器能播、能拖进度 |
| M3 能传能录 | 23 | 上传/录音进素材库，列表可见可删 |
| M4 能合成 | 24 | 输入文字 → 素材库多出一条 AI 语音 |
| M5 能编排 | 25 | 拖块 → 保存 → 刷新还在 → 串播整条时间轴 |

---

## 8. 卡住了怎么办（本项目的自救手册）

纯文档跟做，卡住是正常的。按这个顺序自救，90% 的问题到第 3 步就解决了：

1. **退级**：回到上一个里程碑，确认它还是好的（比如 M3 卡住 → 先验证 M2 的播放器还能播）。
   如果上一级也坏了，说明问题出在你最近改的东西——Git 看 diff（02 章：`git diff`）
2. **分边**：打开 F12 Network（16 章的黄金分界法）——请求发出去了吗？后端回了什么？
   一分钟定位问题在前端还是后端
3. **对表**：每章末尾都有"常见错误与排查"表，你撞的坑大概率在里面
4. **最小化复现**：把出问题的功能剥离到一个单独的小 html/py 文件里单独跑——
   剥离的过程往往自己就发现了问题
5. **正确地求助**：带着三样东西提问（问 AI 或人都一样）——
   ① 完整报错原文 ② 相关代码片段 ③ 你已经试过什么。
   "不行了/报错了"三个字的提问，谁也帮不了你

> 最重要的心态：**卡住不是走错了路，是走到了自己能力边界——边界就是这么推出去的。**

---

## 常见疑问

| 疑问 | 回答 |
|---|---|
| 我完全不懂音乐/声学，能做吗？ | 能。第 1 节的表就是全部理论需求，剩下都是你学过的 Web 开发 |
| 为什么不直接上 Web Audio API？ | 它是"专业调音台"，学习曲线陡。`<audio>` 是"播放器"，本项目的需求它全覆盖。25 章末尾会告诉你什么时候才需要升级 |
| uploads/ 要进 Git 吗？ | 不要（用户数据不进版本库），但要提交一个空的 `uploads/.gitkeep` 占位 |
| 将来文件多了怎么办？ | 路径在数据库里，换云存储（OSS/S3）时只改"存"和"取"两个函数——这正是第 4 节决策的红利 |

---

## 小练习（交付 M1）

1. 按 7.1 结构建好 `audiobook/` 项目骨架（venv、依赖、包结构、uploads/），
   database.py 抄 7.2、index.html 抄 7.3。
2. 按 7.4 把**两个终端**都跑起来：后端 /docs 能打开、前端空页面五个区块可见、
   浏览器 Console 无红字（验证 CORS 和模块加载都正常）。
3. 用 `sqlite3` 命令行（05 章技能）手动 INSERT 一条假 audios 记录和一条引用它的 clips 记录；
   再试着 INSERT 一条 `audio_id=999` 的 clips——观察外键报错长什么样。
4. 写出第 5 节那条 JOIN 查询，确认能查出"块+素材名"的拼接结果。

> 下一章：[22 · 音频播放](22-audio-playback.md) —— 让第一段声音从你的网页里响起来。
