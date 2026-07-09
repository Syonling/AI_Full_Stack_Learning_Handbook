# 06 · FastAPI 进阶

> 本章目标：掌握让 API 变得"专业"的能力——数据校验、错误处理、状态码、CORS、依赖注入。
> 预计学习时间：3~4 小时。建议先学完第 04 章。

---

## 学习目标

1. 用 Pydantic 做精细的数据校验（长度、范围、格式）
2. 用 `response_model` 控制返回给客户端的数据
3. 正确使用 HTTP 状态码
4. 用 `HTTPException` 返回错误
5. 配置 CORS（前后端分离必备）
6. 理解依赖注入 `Depends`（为数据库连接做准备）

---

## 1. Pydantic 模型进阶

### 1.1 字段校验 Field

```python
from pydantic import BaseModel, Field

class TodoCreate(BaseModel):
    # ... 表示必填；min_length/max_length 限制长度
    title: str = Field(..., min_length=1, max_length=100)
    # ge = 大于等于, le = 小于等于 (greater/less than or equal)
    priority: int = Field(default=1, ge=1, le=5)
    # 描述会显示在 /docs 文档里
    description: str = Field(default="", description="detailed notes")
```

客户端发来 `{"title": "", "priority": 99}` 时，FastAPI 自动返回 422，
并逐条说明：title 太短、priority 超出范围。**你一行校验代码都不用写。**

### 1.2 嵌套模型

```python
class Tag(BaseModel):
    name: str

class TodoCreate(BaseModel):
    title: str
    tags: list[Tag] = []        # 模型嵌套模型

# 对应的 JSON：
# {"title": "shopping", "tags": [{"name": "life"}, {"name": "urgent"}]}
```

### 1.3 模型对象的常用操作

```python
todo = TodoCreate(title="learn", priority=3)

todo.title                  # 像属性一样访问字段
todo.model_dump()           # 转成 dict：{"title": "learn", "priority": 3, ...}
todo.model_dump_json()      # 转成 JSON 字符串

# 从字典创建模型（会触发校验，数据不合法时抛 ValidationError）
data = {"title": "learn", "priority": 3}
todo2 = TodoCreate(**data)
```

---

## 2. 响应模型 response_model

`response_model` 定义"**返回给客户端的数据长什么样**"，多余的字段会被自动过滤——
最典型的用途是**隐藏敏感字段**（如密码）。

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserIn(BaseModel):        # 客户端发来的：带密码
    username: str
    password: str

class UserOut(BaseModel):       # 返回给客户端的：不带密码
    username: str

@app.post("/users", response_model=UserOut)
def create_user(user: UserIn):
    # 即使这里返回了包含 password 的完整数据，
    # response_model 也会把 password 过滤掉
    return user
```

常见的"一套资源三个模型"命名习惯：

```python
class TodoCreate(BaseModel):    # POST 时客户端发来的（没有 id）
    title: str
    done: bool = False

class TodoUpdate(BaseModel):    # PUT 时客户端发来的（字段都可选）
    title: str | None = None
    done: bool | None = None

class TodoOut(BaseModel):       # 返回给客户端的（有 id）
    id: int
    title: str
    done: bool
```

---

## 3. HTTP 状态码

状态码告诉客户端"这次请求的结果如何"。最常用的：

| 状态码 | 含义 | 典型场景 |
|---|---|---|
| 200 OK | 成功（默认） | GET / PUT 成功 |
| 201 Created | 创建成功 | POST 成功 |
| 204 No Content | 成功且无返回内容 | DELETE 成功 |
| 400 Bad Request | 请求有问题 | 业务规则不满足 |
| 404 Not Found | 资源不存在 | 查询的 id 不存在 |
| 422 Unprocessable Entity | 数据校验失败 | FastAPI 自动返回 |
| 500 Internal Server Error | 服务器代码出错 | 你的代码抛了未处理的异常 |

指定成功时的状态码：

```python
from fastapi import FastAPI, status

app = FastAPI()

@app.post("/todos", status_code=status.HTTP_201_CREATED)   # 也可以直接写 201
def create_todo():
    return {"message": "created"}

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int):
    return None      # 204 表示无内容，返回 None
```

---

## 4. 错误处理 HTTPException

业务逻辑中发现问题时（如"找不到这条记录"），**抛出 `HTTPException`**：

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

fake_db = {1: {"title": "learn fastapi"}}

@app.get("/todos/{todo_id}")
def get_todo(todo_id: int):
    if todo_id not in fake_db:
        # raise 之后函数立即结束，客户端收到 404 和错误信息
        raise HTTPException(status_code=404, detail=f"todo {todo_id} not found")
    return fake_db[todo_id]
```

客户端收到：

```json
// HTTP 404
{"detail": "todo 1 not found"}
```

> **要点**：是 `raise`（抛出），不是 `return`。
> 用 return 返回 HTTPException 是初学者最常见的错误——那样客户端会收到 200 和一个奇怪的对象。

---

## 5. CORS —— 前后端分离必备

### 问题场景

你的前端页面（比如直接双击打开的 main.html，或跑在 `http://localhost:3000`）
去 fetch 后端 `http://127.0.0.1:8000` 时，浏览器会报错：

```
Access to fetch ... has been blocked by CORS policy
```

这是浏览器的同源安全策略：**默认禁止网页请求"别的来源"的接口**。
后端需要显式声明"我允许哪些来源访问"：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 允许所有来源（学习阶段方便；生产环境要写具体域名）
    allow_methods=["*"],          # 允许所有 HTTP 方法
    allow_headers=["*"],          # 允许所有请求头
)
```

> **要点**：学习阶段直接 `["*"]` 全放开即可；
> 上线时应改成具体地址，如 `allow_origins=["https://myapp.com"]`。

---

## 6. 依赖注入 Depends

**依赖注入 = 把"很多接口都需要的准备工作"抽成一个函数，让 FastAPI 自动帮你调用。**

没有依赖注入时，每个接口都要重复写同样的代码：

```python
@app.get("/todos")
def list_todos():
    conn = create_connection()      # 重复
    ...

@app.post("/todos")
def create_todo():
    conn = create_connection()      # 重复
    ...
```

用 `Depends` 改造：

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# 依赖函数：yield 之前 = 准备工作，yield 之后 = 收尾工作
def get_db():
    conn = create_connection()
    try:
        yield conn                  # 把 conn 交给路由函数使用
    finally:
        conn.close()                # 请求结束后自动关闭（哪怕出错也会执行）

@app.get("/todos")
def list_todos(db = Depends(get_db)):      # FastAPI 自动调用 get_db 并注入结果
    ...

@app.post("/todos")
def create_todo(db = Depends(get_db)):     # 每个请求都拿到全新的连接
    ...
```

好处：

1. **不重复**：准备/收尾逻辑只写一次
2. **不会忘关**：`finally` 保证连接总能关闭
3. **好测试**：测试时可以替换掉依赖

> 第 07 章会用它管理 SQLite 连接，这是最经典的应用场景。

---

## 7. 其他常用功能速览

### 7.1 文件上传

```python
from fastapi import FastAPI, UploadFile

app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile):
    content = await file.read()               # 读取文件内容（bytes）
    return {"filename": file.filename, "size": len(content)}
```

需要先安装：`pip install python-multipart`

### 7.2 返回静态文件 / 前端页面

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 把 static 文件夹挂载到 /static 路径下
app.mount("/static", StaticFiles(directory="static"), name="static")

# 访问根路径时返回前端页面（前后端一体的简单做法，可避开 CORS 问题）
@app.get("/")
def index():
    return FileResponse("static/index.html")
```

### 7.3 路由分组 APIRouter（项目变大后用）

```python
# ── routers/todos.py ──
from fastapi import APIRouter

router = APIRouter(prefix="/todos", tags=["todos"])

@router.get("")            # 实际路径 = /todos
def list_todos():
    return []

# ── main.py ──
from fastapi import FastAPI
from routers import todos

app = FastAPI()
app.include_router(todos.router)
```

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 前端报 CORS 错误 | 后端没配置 CORSMiddleware | 见第 5 节，加上中间件 |
| 返回 200 但内容是奇怪的对象 | 用 `return HTTPException(...)` | 改成 `raise` |
| response_model 报 500 | 返回的数据缺少模型要求的字段 | 检查返回值包含模型的所有必填字段 |
| `Form data requires "python-multipart"` | 上传文件没装依赖 | `pip install python-multipart` |
| 422 但不知道哪错了 | —— | 读响应里的 `detail` 数组，`loc` 指出错误字段位置 |

---

## 小练习

1. 给 `TodoCreate` 加上校验：`title` 长度 1~50，`priority` 范围 1~5。故意发一个非法数据，观察 422 响应的内容。
2. 写一个 `GET /todos/{todo_id}`，todo_id 大于 100 时抛 404。
3. 定义 `UserIn`（含 password）和 `UserOut`（不含），用 `response_model` 验证密码确实被过滤。
4. 给你的应用加上 CORS 中间件，然后用一个本地 HTML 文件 fetch 它，确认不再报 CORS 错误。

> 下一章：[07 · FastAPI + SQLite 整合](07-fastapi-sqlite-crud.md)（需要先学 [05 · SQLite 基础](05-sqlite-basics.md)）。
