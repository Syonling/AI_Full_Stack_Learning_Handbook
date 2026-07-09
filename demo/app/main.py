"""FastAPI 应用入口：五个 CRUD 路由 + 生产四件套（日志/中间件/异常兜底/lifespan）。

对应文档：
    CRUD 路由        → docs/07-fastapi-sqlite-crud.md 第 4 节（逐行讲解）
    日志配置         → docs/03-logging-and-debugging.md
    配置读取         → docs/08-config-and-env.md
    中间件/异常/lifespan → docs/09-fastapi-engineering.md

运行方式（在 app/ 目录下）：
    uvicorn main:app --reload
然后打开 http://127.0.0.1:8000/docs 交互测试。
"""
import logging
import sqlite3
import time
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import get_db, init_db
from schemas import TodoCreate, TodoOut, TodoUpdate

# ── 日志配置（docs/03）：入口处配置一次，全项目生效 ──────────
logging.basicConfig(
    level=settings.log_level,        # 来自 .env / 环境变量，默认 INFO
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ── lifespan（docs/09 第 3 节）：启动/关闭钩子 ────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()                        # 启动时建表（已存在则跳过）
    logger.info("database ready, %s starting", settings.app_name)
    yield                            # ← 应用在这里运行
    logger.info("app shutting down")


app = FastAPI(
    title=settings.app_name,
    description="FastAPI + SQLite learning demo",
    lifespan=lifespan,
)

# 允许任意来源跨域访问（学习用；生产环境应写具体域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 请求日志中间件（docs/09 第 1 节）──────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)          # 交给路由处理
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1fms)",
        request.method, request.url.path, response.status_code, elapsed_ms,
    )
    return response


# ── 全局异常兜底（docs/09 第 2 节）────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # 完整堆栈进日志（给开发者）；干净 JSON 给客户端（不泄露内部细节）
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "internal server error"})


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
    logger.info("todo %s created", new_id)       # 关键业务事件记一条 INFO
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


# ── 后台任务示例（docs/09 第 4 节）────────────────────────────
def write_reminder_log(todo_id: int):
    """模拟耗时工作（发邮件/推送等）——在响应返回之后才执行。"""
    time.sleep(2)
    logger.info("reminder for todo %s has been processed", todo_id)


@app.post("/todos/{todo_id}/remind", status_code=status.HTTP_202_ACCEPTED)
def remind_todo(
    todo_id: int,
    background_tasks: BackgroundTasks,
    db: sqlite3.Connection = Depends(get_db),
):
    row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"todo {todo_id} not found")
    background_tasks.add_task(write_reminder_log, todo_id)   # 不让用户等
    return {"message": "reminder scheduled"}                  # 立即返回 202
