# 07 · FastAPI + SQLite 整合：完整 CRUD API

> 本章目标：把前几章的知识拼起来，构建一个完整的、数据真正落盘的 Todo API。
> 本章的 CRUD 代码与 [demo/](../demo/) 文件夹**逐行对应**——建议边读边对照运行。
> （demo 里还多出 config.py、日志中间件等"生产四件套"，那是第 08、09 章的内容，先忽略即可。）
> 预计学习时间：4~5 小时。

---

## 学习目标

1. 设计多文件项目结构（database / schemas / main 分离）
2. 用依赖注入管理 SQLite 连接的生命周期
3. 实现完整的 CRUD 五个接口
4. 掌握 `sqlite3.Row → dict → JSON` 的数据转换链路
5. 处理"资源不存在"等真实业务场景

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

## 小练习（增强这个 demo）

1. 给 `GET /todos` 增加 `offset: int = 0` 查询参数，实现分页（`LIMIT ? OFFSET ?`）。
2. 增加 `GET /todos/search?keyword=xxx` 接口，用 `LIKE` 模糊搜索 title。
3. 给表增加 `created_at` 字段（提示：`TEXT DEFAULT (datetime('now'))`），
   删掉旧的 todos.db 重启后观察效果。
4. 增加 `DELETE /todos` 接口（清空所有），并思考：这样的接口危险吗？该不该做二次确认？

> 下一章：[06 · 测试与项目结构](10-testing-and-structure.md) —— 让你的代码可验证、可扩展。
