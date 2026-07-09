# 04 · FastAPI 入门

> 本章目标：写出你的第一个 API，掌握路由、路径参数、查询参数、请求体四大核心概念。
> 预计学习时间：3~4 小时。
::: details 关联教程
[1小时精通Python的FastAPI框架的所有知识点](https://www.bilibili.com/video/BV18F4m1K7N3)
:::
---

## 学习目标

1. 安装 FastAPI，用 `uvicorn` 启动服务器
2. 理解什么是路由（route）和 HTTP 方法（GET / POST / PUT / DELETE）
3. 掌握三种接收数据的方式：**路径参数、查询参数、请求体**
4. 会用自动文档 `/docs` 测试自己的接口

---

## 1. 什么是 FastAPI？

FastAPI 是一个 Python Web 框架，用来编写 **HTTP API**（前端页面通过网络请求调用的后端接口）。

它的三大特点：

- **快**：性能是 Python 框架中最高的一档
- **省**：基于类型注解自动完成参数解析、数据校验、文档生成
- **自带交互文档**：写完接口，浏览器打开 `/docs` 就能直接测试

一次请求的完整流程：

```
浏览器/前端                        FastAPI 后端
    │                                  │
    │  ── HTTP 请求（GET /todos）──▶   │  找到匹配的路由函数
    │                                  │  执行函数，得到返回值
    │  ◀── HTTP 响应（JSON 数据）──    │  自动把返回值转成 JSON
```

---

## 2. 安装与启动

```bash
# 激活虚拟环境后安装（uvicorn 是运行 FastAPI 的服务器）
pip install fastapi uvicorn
```

最小可运行的 FastAPI 应用，保存为 `main.py`：

```python
from fastapi import FastAPI

app = FastAPI()          # 创建应用实例

@app.get("/")            # 装饰器：把下面的函数注册为 GET / 的处理函数
def read_root():
    return {"message": "Hello, FastAPI!"}    # 字典会自动转成 JSON
```

启动服务器：

```bash
# main 是文件名（main.py），app 是代码里的变量名
# --reload 表示改代码后自动重启（只在开发时用）
uvicorn main:app --reload
```

启动成功后：

- 打开 <http://127.0.0.1:8000> —— 看到 `{"message": "Hello, FastAPI!"}`
- 打开 <http://127.0.0.1:8000/docs> —— 自动生成的**交互式 API 文档**（重要！）

> **要点**：`uvicorn main:app --reload` 这条命令要在 `main.py` 所在的文件夹里执行。
> 按 `Ctrl + C` 停止服务器。

---

## 3. 路由与 HTTP 方法

一个"路由"= **HTTP 方法 + 路径 + 处理函数**。四个最常用的 HTTP 方法各有语义：

| 方法 | 语义 | 例子 |
|---|---|---|
| GET | 读取数据 | 获取待办列表 |
| POST | 新建数据 | 添加一条待办 |
| PUT | 更新数据 | 修改一条待办 |
| DELETE | 删除数据 | 删除一条待办 |

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/todos")           # 读取
def list_todos():
    return [{"id": 1, "title": "learn fastapi"}]

@app.post("/todos")          # 新建
def create_todo():
    return {"message": "created"}

@app.put("/todos/{todo_id}")     # 更新
def update_todo(todo_id: int):
    return {"message": f"updated {todo_id}"}

@app.delete("/todos/{todo_id}")  # 删除
def delete_todo(todo_id: int):
    return {"message": f"deleted {todo_id}"}
```

> **要点**：同一个路径可以注册多个不同方法的路由（如 GET /todos 和 POST /todos 互不冲突）。

---

## 4. 路径参数（Path Parameters）

路径中用 `{}` 占位，值会作为参数传入函数。**类型注解决定了自动转换和校验**。

```python
@app.get("/todos/{todo_id}")
def get_todo(todo_id: int):          # 注解为 int
    return {"todo_id": todo_id}
```

- 访问 `/todos/5` → `{"todo_id": 5}`（字符串 "5" 自动转成整数 5）
- 访问 `/todos/abc` → FastAPI 自动返回 422 错误，提示类型不合法——**你不用写任何校验代码**

多个路径参数：

```python
@app.get("/users/{user_id}/todos/{todo_id}")
def get_user_todo(user_id: int, todo_id: int):
    return {"user_id": user_id, "todo_id": todo_id}
```

> **坑**：固定路径要写在动态路径**前面**。
> `/todos/all` 必须注册在 `/todos/{todo_id}` 之前，否则 "all" 会被当成 todo_id 而报错。

---

## 5. 查询参数（Query Parameters）

URL 中 `?` 后面的部分，如 `/todos?done=true&limit=10`。
**函数参数中没有出现在路径 `{}` 里的，自动成为查询参数**。

```python
@app.get("/todos")
def list_todos(done: bool | None = None, limit: int = 10):
    result = f"filter done={done}, limit={limit}"
    return {"query": result}
```

- `/todos` → done=None, limit=10（使用默认值）
- `/todos?limit=5` → done=None, limit=5
- `/todos?done=true&limit=5` → done=True, limit=5

规则总结：

| 写法 | 含义 |
|---|---|
| `limit: int` | 必填查询参数（不传会报 422） |
| `limit: int = 10` | 可选，默认 10 |
| `done: bool \| None = None` | 可选，不传时为 None |

---

## 6. 请求体（Request Body）—— 接收 JSON 数据

POST / PUT 请求通常携带 JSON 数据。用 **Pydantic 模型**定义数据结构：

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 定义"客户端应该发什么样的数据"
class TodoCreate(BaseModel):
    title: str                    # 必填字符串
    description: str = ""         # 选填，默认空字符串
    done: bool = False            # 选填，默认 False

@app.post("/todos")
def create_todo(todo: TodoCreate):        # 注解为模型类 → 自动从请求体解析
    return {"received": todo.model_dump()}  # model_dump() 把模型转回字典
```

前端发送（对应你 main.html 里的 fetch 写法）：

```javascript
fetch("/todos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: "learn fastapi", done: false })
});
```

FastAPI 自动完成：

1. 读取请求体的 JSON
2. 校验字段类型（`title` 不是字符串？缺少必填字段？→ 自动返回 422 和详细错误说明）
3. 转换成 `TodoCreate` 对象传给你的函数

> **要点**：三种参数可以混用，FastAPI 按规则自动区分——
> **在路径里 → 路径参数；是 Pydantic 模型 → 请求体；其余 → 查询参数。**

```python
@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, todo: TodoCreate, notify: bool = False):
    #             ↑路径参数      ↑请求体            ↑查询参数
    return {"id": todo_id, "data": todo.model_dump(), "notify": notify}
```

---

## 7. 用 /docs 测试接口（重要习惯！）

启动服务器后打开 <http://127.0.0.1:8000/docs>：

1. 每个接口都列在页面上，点开可以看到参数说明
2. 点 **Try it out** → 填参数 → **Execute**，直接发请求看结果
3. 页面还显示等价的 `curl` 命令，可以复制到终端执行

这是 FastAPI 最好用的功能——**写完接口马上测**，不需要写任何前端代码。

用 curl 在终端测试（等价方式）：

```bash
# GET
curl "http://127.0.0.1:8000/todos?limit=5"

# POST（发送 JSON）
curl -X POST "http://127.0.0.1:8000/todos" \
  -H "Content-Type: application/json" \
  -d '{"title": "learn fastapi", "done": false}'
```

---

## 8. 返回值的规则

路由函数可以直接返回这些类型，FastAPI 自动转成 JSON：

```python
@app.get("/examples")
def examples():
    return {"key": "value"}       # dict → JSON object

# 也可以返回：
# 列表        → JSON array，如 [{"id": 1}, {"id": 2}]
# Pydantic 模型 → 自动转 JSON object
# 字符串/数字   → 原样返回，如 "hello" / 42
```

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `Error loading ASGI app. Could not import module "main"` | uvicorn 命令在错误的文件夹里执行 | `cd` 到 main.py 所在文件夹再运行 |
| 返回 `{"detail":"Not Found"}` | 请求的路径没有对应路由 | 检查路径拼写；到 /docs 看已注册的路由 |
| 返回 `{"detail":"Method Not Allowed"}` | 路径对了但 HTTP 方法不对 | 比如你用 GET 访问了只有 POST 的路由 |
| 返回 422 Unprocessable Entity | 参数类型不符 / 缺少必填字段 | 看返回的 detail 里的具体说明——它会精确告诉你哪个字段错了 |
| 改了代码没生效 | 启动时没加 `--reload` | 加上 `--reload`，或手动重启 |
| 端口被占用 `Address already in use` | 上一个服务器没关 | 关掉旧终端，或换端口 `uvicorn main:app --port 8001` |

---

## 小练习

1. 写一个 `GET /hello/{name}` 接口，返回 `{"message": "Hello, <name>!"}`。
2. 写一个 `GET /calc` 接口，接收查询参数 `a: int`、`b: int`，返回它们的和。
3. 定义 Pydantic 模型 `Book`（字段：`title: str`、`author: str`、`price: float`），
   写一个 `POST /books` 接口接收它并原样返回。
4. 全部用 `/docs` 页面测一遍，再用 curl 测一遍。

> 下一章可以先跳到 [05 · SQLite 基础](05-sqlite-basics.md) 学数据库，
> 也可以继续 [06 · FastAPI 进阶](06-fastapi-advanced.md)。推荐顺序：04 → 05 → 06 → 07。
