# 01 · Python 后端基础

> 本章目标：掌握写 FastAPI 后端之前必须会的 Python 基础工具和语法。
> 预计学习时间：2~3 小时（边看边敲代码）。
<details>
<summary>关联教程</summary>
[Kaggle-Python](https://www.kaggle.com/learn/python)
</details>
---

## 学习目标

学完本章你将会：

1. 用 `venv` 创建独立的 Python 环境，用 `pip` 安装依赖
2. 看懂并使用**类型注解**（FastAPI 的核心机制）
3. 熟练操作字典（dict）和列表（list）—— 后端数据的基本形态
4. 理解 `async / await` 是什么（FastAPI 路由函数常用）
5. 会用 `try / except` 处理异常
6. 理解模块导入（`import`），为多文件项目做准备

---

## 1. 虚拟环境 venv 与 pip

### 为什么需要虚拟环境？

不同项目可能依赖不同版本的库。虚拟环境（virtual environment）给每个项目一个**独立的依赖空间**，互不干扰。

### 常用命令（macOS / zsh）

```bash
# 1. 在项目文件夹里创建虚拟环境（会生成一个 .venv 文件夹）
python3 -m venv .venv

# 2. 激活虚拟环境（激活后命令行前面会出现 (.venv) 标记）
source .venv/bin/activate

# 3. 安装依赖
pip install fastapi uvicorn

# 4. 查看已安装的包
pip list

# 5. 把当前依赖导出到文件（方便别人复现环境）
pip freeze > requirements.txt

# 6. 根据文件安装全部依赖
pip install -r requirements.txt

# 7. 退出虚拟环境
deactivate
```

> **要点**：每次打开新终端开始工作前，先 `source .venv/bin/activate` 激活环境。

---

## 2. 类型注解（Type Hints）

类型注解告诉阅读者（和工具）"这个变量/参数/返回值应该是什么类型"。
**FastAPI 完全依赖类型注解**来做参数解析和数据校验，必须掌握。

```python
# 变量注解
name: str = "Alice"
age: int = 25
price: float = 9.99
is_done: bool = False

# 函数参数和返回值注解
def greet(name: str) -> str:
    return f"Hello, {name}!"

# 容器类型注解
tags: list[str] = ["python", "fastapi"]
scores: dict[str, int] = {"math": 90, "english": 85}

# 可选类型：值可以是 str，也可以是 None
def find_user(user_id: int) -> str | None:
    if user_id == 1:
        return "Alice"
    return None   # 没找到

# 带默认值的参数
def paginate(page: int = 1, size: int = 10) -> dict:
    return {"page": page, "size": size}
```

> **要点**：Python 的类型注解在运行时**不强制**（传错类型不会直接报错），
> 但 FastAPI 会利用它做**真正的校验**——这就是 FastAPI 好用的原因。

---

## 3. 字典与列表 —— 后端数据的基本形态

后端 API 收发的 JSON 数据，在 Python 里就是**字典和列表的组合**。

### 字典 dict（对应 JSON 的 object）

```python
user = {"id": 1, "name": "Alice", "age": 25}

# 读取
print(user["name"])            # Alice（键不存在会报 KeyError）
print(user.get("email"))       # None（键不存在返回 None，更安全）
print(user.get("email", ""))   # 空字符串（可指定默认值）

# 写入 / 修改
user["email"] = "alice@example.com"
user["age"] = 26

# 删除
del user["age"]

# 遍历
for key, value in user.items():
    print(key, "=", value)

# 判断键是否存在
if "name" in user:
    print("has name")
```

### 列表 list（对应 JSON 的 array）

```python
todos = [
    {"id": 1, "title": "learn python", "done": True},
    {"id": 2, "title": "learn fastapi", "done": False},
]

# 增
todos.append({"id": 3, "title": "learn sqlite", "done": False})

# 查：索引和切片
first = todos[0]        # 第一个
last = todos[-1]        # 最后一个
top2 = todos[:2]        # 前两个

# 遍历
for todo in todos:
    print(todo["title"])

# 列表推导式（很常用！从列表生成新列表）
titles = [t["title"] for t in todos]                 # 提取所有标题
undone = [t for t in todos if not t["done"]]         # 过滤未完成的

# 查找单个元素（找不到返回 None）
target = next((t for t in todos if t["id"] == 2), None)

# 长度
count = len(todos)
```

> **要点**：`[表达式 for 元素 in 列表 if 条件]` 这个列表推导式在后端代码里极其常见，
> 比如"把数据库查出来的每一行转成字典"。

---

## 4. 函数与 async / await 初识

### 普通函数 vs 异步函数

```python
# 普通（同步）函数
def read_data() -> dict:
    return {"msg": "hello"}

# 异步函数：def 前面加 async
async def read_data_async() -> dict:
    return {"msg": "hello"}
```

### 什么时候用 async？

- **同步函数**：执行时会"堵住"，做完一件事才能做下一件
- **异步函数**：遇到等待（如网络请求、读文件）时可以先去处理别的请求，效率更高

在 FastAPI 中，两种写法都可以做路由函数：

```python
@app.get("/sync")
def sync_route():
    return {"type": "sync"}      # FastAPI 会放到线程池里跑，不会卡

@app.get("/async")
async def async_route():
    return {"type": "async"}     # 原生异步
```

> **0 基础阶段的建议**：先不用纠结两者区别。
> 规则很简单——**如果函数体内用了 `await`，就必须写 `async def`；否则写普通 `def` 就行。**

```python
import asyncio

async def slow_task() -> str:
    await asyncio.sleep(1)       # 模拟耗时操作，await 只能出现在 async 函数里
    return "done"
```

---

## 5. 异常处理 try / except

后端代码必须处理"意外情况"（用户传错数据、数据库找不到记录……），否则程序会直接崩溃。

```python
# 基本结构
try:
    result = 10 / 0
except ZeroDivisionError:
    print("cannot divide by zero")

# 捕获多种异常 + 获取异常对象
try:
    user = {"name": "Alice"}
    print(user["age"])
except KeyError as e:
    print(f"missing key: {e}")
except Exception as e:           # Exception 兜底捕获所有常规异常
    print(f"unexpected error: {e}")

# finally：无论是否出错都会执行（常用于清理资源，如关闭数据库连接）
try:
    f = open("data.txt")
    content = f.read()
except FileNotFoundError:
    print("file not found")
finally:
    print("cleanup done")

# 主动抛出异常
def set_age(age: int):
    if age < 0:
        raise ValueError("age cannot be negative")
```

> **要点**：在 FastAPI 中你会经常用 `raise HTTPException(status_code=404, detail="...")`
> 来向客户端返回错误——本质上就是"主动抛异常"，详见第 06 章。

---

## 6. 模块与导入 import

项目变大后，代码要拆分到多个文件（模块）里。

```
my_project/
├── main.py          # 入口
├── database.py      # 数据库相关
└── schemas.py       # 数据模型
```

```python
# ── database.py ──
def get_connection():
    return "connection object"

DB_NAME = "app.db"
```

```python
# ── main.py ──

# 方式 1：导入整个模块，用 模块名.成员 访问
import database
conn = database.get_connection()

# 方式 2：只导入需要的成员（更常用）
from database import get_connection, DB_NAME
conn = get_connection()

# 方式 3：导入时起别名
import database as db
conn = db.get_connection()
```

> **要点**：`from x import y` 中的 `x` 是**文件名去掉 .py**。
> 两个文件必须在同一个文件夹（或正确的包结构）下才能这样导入。

---

## 7. f-string 字符串格式化

后端代码里拼接消息、日志时最常用的写法：

```python
name = "Alice"
count = 3

msg = f"user {name} has {count} todos"        # 变量直接嵌入
price = f"total: {19.9 * 2:.2f}"              # 保留两位小数 → total: 39.80
debug = f"{name=}"                            # 调试技巧 → name='Alice'
```

---

## 常见错误与排查

| 错误信息 | 原因 | 解决 |
|---|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | 没激活虚拟环境，或没安装 | `source .venv/bin/activate` 再 `pip install fastapi` |
| `KeyError: 'xxx'` | 访问了字典里不存在的键 | 改用 `d.get("xxx")` 或先用 `in` 判断 |
| `IndentationError` | 缩进不一致（Tab 和空格混用） | 统一用 4 个空格缩进 |
| `SyntaxError: 'await' outside async function` | 在普通函数里用了 `await` | 函数改成 `async def` |
| `TypeError: 'NoneType' object is not subscriptable` | 对 None 使用了 `[]` 取值 | 先判断 `if x is not None:` |

---

## 小练习

在 `learning_from_claude` 之外自己建一个练习文件试试：

1. 创建一个虚拟环境并激活，`pip install fastapi uvicorn`，然后 `pip list` 确认安装成功。
2. 写一个函数 `filter_done(todos: list[dict]) -> list[dict]`，用列表推导式返回所有 `done == True` 的待办事项。
3. 写一个函数 `get_todo_by_id(todos: list[dict], todo_id: int) -> dict | None`，找不到时返回 `None`。
4. 给第 3 题加上异常处理：如果 `todos` 不是列表就 `raise TypeError`。

> 下一章 [02 · Git 版本控制](02-git-basics.md)——从第一天起，让你写的每一行练习代码都有版本记录。
