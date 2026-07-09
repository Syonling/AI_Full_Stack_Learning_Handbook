# 09 · FastAPI 工程化：中间件、异常处理与生命周期

> 本章目标：给 API 加上"生产必备四件套"——请求日志中间件、全局异常处理、启动/关闭钩子（lifespan）、后台任务。
> 预计学习时间：3~4 小时。需要第 03 章（logging）、第 07 章（整合实战）。demo 已按本章升级，可对照运行。

---

## 学习目标

1. 用**中间件**给每个请求记录访问日志（方法、路径、状态码、耗时）
2. 用**全局异常处理器**兜底：再意外的错误也不给用户看堆栈
3. 用 **lifespan** 管理启动/关闭时机（建表、日志、清理）
4. 会用 **BackgroundTasks** 处理"不用让用户等"的工作
5. 理解 uvicorn 日志和你自己日志的关系

---

## 1. 中间件：每个请求都要过的关卡

**中间件（middleware）= 包在所有路由外面的一层函数**。每个请求进来先经过它，响应出去也经过它——
天然适合做**访问日志、计时、统一加响应头**这类"每个请求都要做"的事。

```python
import logging
import time

from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)
app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)      # ← 交给路由处理，拿到响应

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1fms)",
        request.method,            # GET / POST ...
        request.url.path,          # /todos/3
        response.status_code,      # 200 / 404 ...
        elapsed_ms,
    )
    return response
```

之后每个请求都会留下一行记录：

```
2026-07-09 16:02:11 INFO app.main - GET /todos -> 200 (3.2ms)
2026-07-09 16:02:15 INFO app.main - POST /todos -> 201 (5.8ms)
2026-07-09 16:02:20 INFO app.main - GET /todos/99 -> 404 (1.1ms)
```

结构记忆：`call_next` 之前 = 请求进来时做的事；之后 = 响应出去前做的事。
（是不是很像第 06 章依赖注入里 `yield` 前后的关系？）

> **要点**：中间件必须是 `async def`，且必须 `return response`。
> 排查性能问题时，这行耗时日志是你的第一手线索。

---

## 2. 全局异常处理：永远不给用户看堆栈

没有兜底时，代码里任何没预料到的异常都会让用户收到丑陋的 500 页面，而你却不知道发生过。
两层防线：

### 2.1 业务错误：继续用 HTTPException（第 06 章学过）

可预见的错误（找不到、没权限）在路由里主动抛，这不变。

### 2.2 意外错误：全局兜底处理器

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)          # 捕获所有没人处理的异常
async def unhandled_exception_handler(request: Request, exc: Exception):
    # 完整堆栈进日志（给你看）
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    # 干净的 JSON 给客户端（不泄露内部细节）
    return JSONResponse(
        status_code=500,
        content={"detail": "internal server error"},
    )
```

效果：

- **用户**看到的永远是 `{"detail": "internal server error"}`
- **你**在日志里拿到完整 traceback（`logger.exception` 是第 03 章学的）

也可以为特定异常类单独注册处理器，比如统一改写数据库错误：

```python
import sqlite3

@app.exception_handler(sqlite3.OperationalError)
async def db_error_handler(request: Request, exc: sqlite3.OperationalError):
    logger.exception("database error")
    return JSONResponse(status_code=503, content={"detail": "database unavailable"})
```

> **要点**：`HTTPException` 不会进这个兜底处理器——FastAPI 对它有内置处理（返回你指定的状态码）。
> 兜底器只接"漏网之鱼"。

---

## 3. lifespan：启动与关闭的正确姿势

之前 demo 在模块顶部直接调用 `init_db()`——能用，但"导入即执行副作用"不是好习惯
（比如 pytest 一导入就建表）。正确姿势是 **lifespan**：

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── yield 之前：启动时执行 ──
    init_db()
    logger.info("database ready, app starting")

    yield          # ← 应用在这里运行

    # ── yield 之后：关闭时执行（Ctrl+C / 重启时）──
    logger.info("app shutting down")

app = FastAPI(lifespan=lifespan)
```

又是熟悉的 `yield` 前后结构！适合放在 lifespan 里的事：

| 启动时（yield 前） | 关闭时（yield 后） |
|---|---|
| 建表 / 检查数据库连接 | 关闭连接池 |
| 加载配置、模型、缓存 | 把缓存落盘 |
| 打一条"服务启动"日志 | 打一条"服务停止"日志 |

---

## 4. BackgroundTasks：别让用户等

有些工作**必须做，但用户不需要等它做完**：发邮件、生成报表、调用慢的第三方接口。

```python
from fastapi import BackgroundTasks

def send_welcome_email(email: str):
    """假装发邮件（真实场景可能耗时数秒）。"""
    time.sleep(3)
    logger.info("welcome email sent to %s", email)

@app.post("/users", status_code=201)
def create_user(email: str, background_tasks: BackgroundTasks):
    # ... 保存用户到数据库（这个必须等）...
    background_tasks.add_task(send_welcome_email, email)   # 这个不等
    return {"message": "created"}     # ← 立即返回，邮件在响应之后才发
```

用户在几毫秒内拿到响应；`send_welcome_email` 在**响应发出之后**才执行。

> **要点**：BackgroundTasks 适合"顺手做的小事"。任务失败会丢（进程重启就没了）——
> 需要保证必达的任务（支付回调、重要通知）要用专业任务队列（Celery / arq），现阶段知道边界即可。

---

## 5. uvicorn 日志与你的日志

启动 demo 时你会看到两类日志：

```
INFO:     127.0.0.1:52133 - "GET /todos HTTP/1.1" 200 OK        ← uvicorn 的访问日志
2026-07-09 16:02:11 INFO app.main - GET /todos -> 200 (3.2ms)   ← 你的中间件日志
```

- uvicorn 自带的访问日志（logger 名为 `uvicorn.access`）格式固定、不含耗时
- 你自己的中间件日志可以自由控制格式、级别、输出文件

两者并存没问题；想关掉 uvicorn 的那份避免重复：

```bash
uvicorn main:app --no-access-log        # 只留你自己的中间件日志
```

---

## 6. 对照 demo：四件套的完整落地

demo 的 [app/main.py](../demo/app/main.py) 现在长这样（节选骨架）：

```python
logging.basicConfig(level=settings.log_level, format="...")   # 第 03 章
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):          # 第 3 节：启动建表
    init_db()
    logger.info("database ready")
    yield
    logger.info("shutting down")

app = FastAPI(title=settings.app_name, lifespan=lifespan)     # 配置来自第 08 章

app.add_middleware(CORSMiddleware, ...)    # 第 06 章

@app.middleware("http")                    # 第 1 节：访问日志
async def log_requests(request, call_next): ...

@app.exception_handler(Exception)          # 第 2 节：全局兜底
async def unhandled_exception_handler(request, exc): ...

# ↓ 五个 CRUD 路由与第 07 章完全一致
```

跑起来感受：`cd demo && source .venv/bin/activate && cd app && uvicorn main:app --reload`，
随便请求几个接口，观察访问日志；请求一个不存在的路径 `/nope`，看 404 也被记录。

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 中间件写了没生效 | 少了 `@app.middleware("http")` 或没 return response | 检查装饰器和返回值 |
| 中间件报 `call_next is not defined` | 函数签名不对 | 必须 `async def f(request, call_next)` |
| 404/422 没走全局兜底器 | 它们是 HTTPException 体系，有内置处理 | 正常现象；要定制可给 HTTPException 单独注册处理器 |
| lifespan 里的代码没执行 | 忘了 `FastAPI(lifespan=lifespan)` | 创建 app 时传入 |
| 后台任务没执行 | 忘了参数注入 `background_tasks: BackgroundTasks` | 必须通过参数拿到实例，不能自己 `BackgroundTasks()` |
| 日志每条出现两遍 | uvicorn --reload 下重复配置 / handler 重复添加 | 只在入口 basicConfig 一次 |

---

## 小练习

1. 给中间件加一个响应头 `X-Process-Time`，值为本次耗时毫秒数（提示：`response.headers["..."] = ...`），
   用浏览器 DevTools 或 `curl -i` 验证。
2. 在 demo 里临时写一个必炸的路由 `@app.get("/boom")`（函数体 `1/0`），
   验证：客户端收到干净的 500 JSON，日志里有完整堆栈。测完删掉。
3. 给 demo 加一个 `POST /todos/{id}/remind` 接口，用 BackgroundTasks 模拟 3 秒后打一条提醒日志，
   确认接口是立即返回的。
4. 把 demo 的启动命令换成 `--no-access-log`，对比日志输出的变化。

> 下一章：[10 · 测试与项目结构](10-testing-and-structure.md) —— 用自动化测试守住这些工程化成果。
