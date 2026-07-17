# 07 · FastAPI + SQLite 整合：完整 CRUD API

> 本章目标：把前几章的知识拼起来，构建一个完整的、数据真正落盘的 Todo API。
> ⚠️ **本章教学代码是 [demo/](../demo/) 的"基础版"**：接口行为完全一致，但 demo 本身已按
> 08/09 章升级（配置、日志、lifespan 等），**部分代码行和本章不同——具体差异见第 6 节的对照表**。
> 学本章时一律以本章代码为准；demo 用来跑起来玩。
> 预计学习时间：4~5 小时。

---

## 学习目标

1. 设计多文件项目结构（database / schemas / main 分离）
2. 用依赖注入管理 SQLite 连接的生命周期
3. 实现完整的 CRUD 五个接口
4. 掌握 `sqlite3.Row → dict → JSON` 的数据转换链路
5. 处理"资源不存在"等真实业务场景

---

## 0. 本章的正确打开方式：三遍法

本章下面有完整的参考代码——**但它是"参考答案"，不是"阅读材料"**。
直接往下读然后复制粘贴，你会"全都看懂了，什么都没学会"。正确用法：

> **第一遍 · 自己搭**：只看下面的「任务规格卡」，**别往下翻**，凭 04/05/06 章的知识自己写。
> 每一步卡住超过 30 分钟，才允许翻到对应小节看参考。
>
> **第二遍 · 对照**：拿你的实现和本章的逐行讲解做 diff——**差异处就是你的知识缺口**，
> 逐个搞懂"参考代码为什么这么写"。
>
> **第三遍 · 重写**：合上书、关掉 demo，从空文件夹再写一遍。写不出的地方，回去补对应章节。

### 任务规格卡（第一遍只看这里）

**目标**：Todo API——本章开头那张接口表的 5 个接口，数据存 SQLite。

**施工顺序**（每一步都可运行、可验证，别跳步）：

| 步骤 | 做什么 | 用到的知识 | 验收标准 |
|---|---|---|---|
| ① | `database.py`：建表函数 + get_db 依赖 | 05 章建表/连接、06 章第 6 节 yield 依赖 | `python3 -c "from database import init_db; init_db()"` 后出现 todos.db，`sqlite3` 命令行能看到表 |
| ② | `schemas.py`：Create / Update / Out 三个模型 | 06 章第 1、2 节 | `python3 -c "from schemas import TodoCreate; print(TodoCreate(title='hi'))"` 不报错 |
| ③ | `main.py`：先只写 `GET /todos` 一个接口，跑通 | 04 章路由、06 章 Depends | /docs 里能调用，返回 `[]` |
| ④ | 依次追加 POST → GET 单条 → PUT → DELETE，**每加一个测一个** | 06 章 HTTPException/状态码 | 每个接口在 /docs 验证后再写下一个 |
| ⑤ | 重启服务再查询 | —— | 数据还在（落盘成功）|

提示：卡在"第一行写什么"时，回看每步"用到的知识"那一章的代码示例——**允许翻旧章节，不允许翻本章下文**。

---

## 1. 项目结构

```
demo/
├── requirements.txt      # 依赖清单
└── app/
    ├── main.py           # FastAPI 应用：路由都在这里
    ├── database.py       # SQLite：连接、建表、依赖函数
    └── schemas.py        # Pydantic：请求/响应数据模型
```

为什么拆三个文件？——**各管一摊，改哪类东西去哪个文件**：

- 改数据库表结构 → `database.py`
- 改接口收发的数据格式 → `schemas.py`
- 改接口逻辑 → `main.py`

API 设计（RESTful 风格，业界通用约定）：

| 方法 + 路径 | 功能 | 成功状态码 |
|---|---|---|
| `GET /todos` | 列出所有待办（支持过滤） | 200 |
| `GET /todos/{id}` | 查单条 | 200（不存在 404） |
| `POST /todos` | 新建 | 201 |
| `PUT /todos/{id}` | 更新 | 200（不存在 404） |
| `DELETE /todos/{id}` | 删除 | 204（不存在 404） |

---

## 2. database.py —— 数据库层

::: warning 🛠 先试后看
现在暂停。按规格卡第 ① 步自己写：一个 `init_db()`（建 todos 表）+ 一个 `get_db()`（yield 依赖）。
写完（或卡满 30 分钟）再往下对照。
:::

```python
"""SQLite 连接管理与建表。"""
import sqlite3
from pathlib import Path

# 数据库文件放在 app/ 的上一级（demo/todos.db）
# 用 __file__ 定位，保证无论从哪个目录启动 uvicorn，路径都正确
DB_PATH = Path(__file__).resolve().parent.parent / "todos.db"


def init_db() -> None:
    """建表。应用启动时调用一次，IF NOT EXISTS 保证可重复执行。"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            done INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    """FastAPI 依赖函数：每个请求拿到独立连接，请求结束自动关闭。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row      # 让查询结果支持按列名访问
    try:
        yield conn                       # 交给路由函数使用
    finally:
        conn.close()                     # 无论成功还是报错都会关闭
```

**逐点解读：**

- `DB_PATH` 用 `__file__` 计算绝对路径 —— 新手最常踩的坑是用相对路径 `"todos.db"`，
  结果从不同目录启动时数据库文件到处乱建。
- `get_db` 是**生成器依赖**（有 `yield`）：`yield` 前是准备，`yield` 后是收尾，
  对应第 06 章的 `Depends` 知识点。
- 每个请求一个新连接是 sqlite3 + FastAPI 最简单安全的用法
  （sqlite3 连接默认不能跨线程共用）。

---

## 3. schemas.py —— 数据模型层

::: warning 🛠 先试后看
规格卡第 ② 步：三个模型——新建用的（无 id、title 必填）、更新用的（全部字段可选）、
返回用的（含 id）。想想每个字段的类型和默认值，写完再对照。
:::

```python
"""Pydantic 模型：定义 API 收发数据的结构。"""
from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    """POST /todos 的请求体（新建时客户端发来的数据，没有 id）。"""
    title: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    done: bool = False


class TodoUpdate(BaseModel):
    """PUT /todos/{id} 的请求体（所有字段可选，只更新提供的字段）。"""
    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    done: bool | None = None


class TodoOut(BaseModel):
    """所有接口返回的待办数据（数据库里的完整记录，有 id）。"""
    id: int
    title: str
    description: str
    done: bool
```

**逐点解读：**

- 三个模型对应第 06 章讲的"一套资源三个模型"模式。
- `TodoUpdate` 全部字段默认 `None` → 客户端只发想改的字段（部分更新）。
- 数据库里 `done` 是 0/1，Pydantic 的 `done: bool` 会自动把 0/1 转成 false/true。

---

## 4. main.py —— 应用与路由层

::: warning 🛠 先试后看
规格卡第 ③④ 步：先只写 GET /todos 跑通，再一个一个追加其余四个接口、每加一个在 /docs 测一个。
两个难点自己先想：PUT 怎么做"没发的字段保留旧值"？DELETE 怎么判断"id 不存在返回 404"？
:::

```python
"""FastAPI 应用入口：五个 CRUD 路由。"""
import sqlite3

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from database import get_db, init_db
from schemas import TodoCreate, TodoOut, TodoUpdate

init_db()                      # 启动时建表（已存在则跳过）

app = FastAPI(title="Todo API", description="FastAPI + SQLite learning demo")

# 允许任意来源跨域访问（学习用；生产环境应写具体域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 读取列表 ─────────────────────────────────────────────
@app.get("/todos", response_model=list[TodoOut])
def list_todos(
    done: bool | None = None,                    # 查询参数：?done=true 只看已完成
    limit: int = 100,
    db: sqlite3.Connection = Depends(get_db),
):
    if done is None:
        rows = db.execute(
            "SELECT * FROM todos ORDER BY id LIMIT ?", (limit,)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM todos WHERE done = ? ORDER BY id LIMIT ?",
            (int(done), limit),                  # bool → 0/1
        ).fetchall()
    return [dict(row) for row in rows]           # Row → dict，FastAPI 再转 JSON


# ── 读取单条 ─────────────────────────────────────────────
@app.get("/todos/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"todo {todo_id} not found")
    return dict(row)


# ── 新建 ─────────────────────────────────────────────────
@app.post("/todos", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.execute(
        "INSERT INTO todos (title, description, done) VALUES (?, ?, ?)",
        (todo.title, todo.description, int(todo.done)),
    )
    db.commit()                                  # 别忘了提交！
    new_id = cursor.lastrowid                    # 拿到自增 id
    row = db.execute("SELECT * FROM todos WHERE id = ?", (new_id,)).fetchone()
    return dict(row)                             # 把新记录完整返回给客户端


# ── 更新 ─────────────────────────────────────────────────
@app.put("/todos/{todo_id}", response_model=TodoOut)
def update_todo(
    todo_id: int, todo: TodoUpdate, db: sqlite3.Connection = Depends(get_db)
):
    row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"todo {todo_id} not found")

    # 部分更新：客户端没发的字段（None）保留数据库里的旧值
    current = dict(row)
    new_title = todo.title if todo.title is not None else current["title"]
    new_desc = (
        todo.description if todo.description is not None else current["description"]
    )
    new_done = int(todo.done) if todo.done is not None else current["done"]

    db.execute(
        "UPDATE todos SET title = ?, description = ?, done = ? WHERE id = ?",
        (new_title, new_desc, new_done, todo_id),
    )
    db.commit()
    row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    return dict(row)


# ── 删除 ─────────────────────────────────────────────────
@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    db.commit()
    if cursor.rowcount == 0:                     # 没删到任何行 = id 不存在
        raise HTTPException(status_code=404, detail=f"todo {todo_id} not found")
    return None                                  # 204 无返回内容
```

---

## 5. 关键链路详解

### 5.0 先认两张"新面孔"（其实都有出处）

上面的代码里有两个写法，如果你觉得"前面没见过"，出处在这里：

**① `db.execute(...)` 直接链 `.fetchall()`，cursor 去哪了？**
这是 **05 章 8.4 节**教的快捷方式：Connection 的 execute 会自动新建 cursor、执行、
再把 cursor 返回——所以能链式调用 `.fetchall()` / `.fetchone()` / `.lastrowid`。
和 `cursor = db.cursor()` 三步写法完全等价，本章起统一用短的。

**② `done: bool | None = None, limit: int = 100` 这组查询参数哪来的？**
写法本身是 **04 章第 5 节**的原样搬用（那里连例子都是 `/todos?done=true&limit=5`）。
至于**为什么列表接口要这样设计**——这是所有列表类 API 的"标配三问"：

1. 用户会想按什么条件筛？→ 待办最自然的筛选是"完成没完成" → `done` 过滤（可选，不传=全要）
2. 表变大后一次全拖出来行不行？→ 不行 → `limit` 护栏（这也是 05 章 LIMIT 的用武之地）
3. 默认值给多少？→ 不传 done 就不过滤；limit 给个宽松上限 100

以后你自己设计任何"列表接口"，把这三问过一遍，参数就出来了。

### 5.1 数据的完整旅程（以 POST /todos 为例）

```
前端 JSON  ──▶  Pydantic 校验  ──▶  参数化 SQL  ──▶  SQLite 文件
{"title":"x"}   TodoCreate 对象      INSERT ... ?      todos.db

SQLite 文件  ──▶  sqlite3.Row  ──▶  dict  ──▶  response_model 校验  ──▶  前端 JSON
SELECT ...        row 对象      dict(row)      TodoOut                {"id":1,...}
```

记住这条链路，任何 bug 都可以定位到其中某一环。

### 5.2 为什么 INSERT 之后还要 SELECT 一次？

客户端新建数据后通常需要知道**完整的新记录**（尤其是自增 id）。
`INSERT → lastrowid → SELECT` 是最直白的写法；返回完整记录也让 `response_model=TodoOut` 校验通过。

### 5.3 bool 与 0/1 的来回转换

- 写库时：`int(todo.done)` 把 True/False 转成 1/0（SQLite 没有布尔类型）
- 读库时：Pydantic 的 `done: bool` 自动把 1/0 转回 true/false

---

## 6. 运行与测试

### 6.0 先说清楚：本章代码 vs demo 实际代码的差异

demo 是"活的"——它在 08/09 章被升级过。对照时以下面这张表为准，**别拿差异怀疑自己写错了**：

| 文件 | 本章（基础版，学习以此为准） | demo 实际（升级版） | 差异来自 |
|---|---|---|---|
| schemas.py | —— | ✅ **完全一致** | —— |
| database.py | `DB_PATH` 用 `__file__` 自己计算 | 路径和文件名改从 `config.py` 的配置读取 | 08 章 |
| main.py | 顶部直接调用 `init_db()`；只有 5 个 CRUD 路由 | 建表挪进了 `lifespan`；另有日志配置、请求日志中间件、全局异常兜底、`/remind` 后台任务示例；`create_todo` 里多一行 `logger.info(...)` | 03 / 09 章 |

一句话：**五个路由函数的核心逻辑两边完全一致**（唯一例外是 create_todo 里那一行日志）；
差异全部集中在"工程外壳"，等你学到 08/09 章会亲手给自己的版本加上同样的东西——
到那时回头看 demo，就全对上了。

### 6.1 跑起来

```bash
cd demo
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cd app
uvicorn main:app --reload
```

打开 <http://127.0.0.1:8000/docs> 按顺序测试：

1. `POST /todos` 新建两条 → 确认返回 201 和带 id 的完整记录
2. `GET /todos` → 确认列表里有刚才两条
3. `PUT /todos/1` 只发 `{"done": true}` → 确认 title 没变、done 变了（部分更新生效）
4. `GET /todos?done=true` → 确认过滤生效
5. `DELETE /todos/2` → 返回 204；再 `GET /todos/2` → 返回 404
6. **重启服务器再 GET** → 数据还在！（这就是数据库的意义）

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `no such table: todos` | init_db 没执行 / 连了别的 db 文件 | 确认 `init_db()` 在 main.py 顶部调用；用绝对路径 DB_PATH |
| 新建的数据重启后消失 | 忘了 `db.commit()` | 每个写操作后检查 commit |
| `SQLite objects created in a thread can only be used in that same thread` | 全局共享了一个连接 | 用 `get_db` 依赖，每请求一个连接 |
| response_model 报 500 | 返回的 dict 缺字段 / 类型不对 | 确认 `SELECT *` 包含模型全部字段 |
| PUT 把没发的字段清空了 | 没做部分更新逻辑 | 参照 update_todo：None 的字段用旧值 |
| 404 处理不生效，返回了 500 | 忘了 `raise`，写成了 `return HTTPException(...)` | 用 raise |

---

## 小练习

1. **通关检定（三遍法·第三遍）**：合上书、关掉 demo，从空文件夹**计时**重写整个 API——
   45 分钟内独立完成且五个接口全部可用，才算通过本章。没过就找出卡住的步骤，回对应章节补，改天再测。
2. 给 `GET /todos` 增加 `offset: int = 0` 查询参数，实现分页（`LIMIT ? OFFSET ?`）。
3. 增加 `GET /todos/search?keyword=xxx` 接口，用 `LIKE` 模糊搜索 title。
4. 给表增加 `created_at` 字段（提示：`TEXT DEFAULT (datetime('now'))`），
   删掉旧的 todos.db 重启后观察效果。
5. 增加 `DELETE /todos` 接口（清空所有），并思考：这样的接口危险吗？该不该做二次确认？

> 下一章：[06 · 测试与项目结构](10-testing-and-structure.md) —— 让你的代码可验证、可扩展。
