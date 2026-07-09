# 10 · 测试与项目结构

> 本章目标：学会验证自己的接口是否正确，了解项目变大后的组织方式，以及下一步学什么。
> 预计学习时间：2~3 小时。

---

## 学习目标

1. 熟练用 `/docs` 和 `curl` 手动测试接口
2. 用 `TestClient` 写自动化测试（pytest 入门）
3. 了解中大型 FastAPI 项目的标准目录结构
4. 明确下一步的学习路线

---

## 1. 手动测试：/docs 与 curl

### /docs（Swagger UI）

开发时的首选。每写完一个接口：

1. 打开 <http://127.0.0.1:8000/docs>
2. Try it out → 填参数 → Execute
3. 看三样东西：**状态码**、**响应体**、**响应时间**

另一个自动文档 <http://127.0.0.1:8000/redoc> 更适合"阅读"接口文档。

### curl 常用模板

```bash
# GET（-s 静默模式；结尾加 | python3 -m json.tool 可以格式化 JSON 输出）
curl -s "http://127.0.0.1:8000/todos" | python3 -m json.tool

# GET 带查询参数（URL 有 ? & 时必须加引号）
curl -s "http://127.0.0.1:8000/todos?done=true&limit=5"

# POST 发送 JSON
curl -s -X POST "http://127.0.0.1:8000/todos" \
  -H "Content-Type: application/json" \
  -d '{"title": "test from curl"}'

# PUT
curl -s -X PUT "http://127.0.0.1:8000/todos/1" \
  -H "Content-Type: application/json" \
  -d '{"done": true}'

# DELETE（-i 显示响应头，可以看到 204 状态码）
curl -s -i -X DELETE "http://127.0.0.1:8000/todos/1"

# 只看状态码
curl -s -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:8000/todos"
```

---

## 2. 自动化测试：TestClient + pytest

手动测试的问题：改一处代码，所有接口都可能被影响，每次全部手点一遍不现实。
**自动化测试 = 把"手点"写成代码，一条命令全部重跑。**

### 安装

```bash
pip install pytest httpx        # TestClient 依赖 httpx
```

### 写测试（文件名必须以 test_ 开头）

```python
# test_main.py —— 与 main.py 放同一目录
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)      # 不需要启动 uvicorn！直接在内存里调用应用


def test_create_todo():
    response = client.post("/todos", json={"title": "test todo"})
    assert response.status_code == 201          # 断言：不满足就算测试失败
    data = response.json()
    assert data["title"] == "test todo"
    assert data["done"] is False
    assert "id" in data


def test_get_missing_todo_returns_404():
    response = client.get("/todos/999999")
    assert response.status_code == 404


def test_create_then_delete():
    # 先创建
    created = client.post("/todos", json={"title": "to be deleted"}).json()
    todo_id = created["id"]
    # 再删除
    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 204
    # 确认真的没了
    assert client.get(f"/todos/{todo_id}").status_code == 404


def test_validation_error():
    # title 为空字符串，应该被 Pydantic 拦下
    response = client.post("/todos", json={"title": ""})
    assert response.status_code == 422
```

### 运行

```bash
pytest              # 自动发现并运行所有 test_*.py
pytest -v           # 显示每个测试的名字和结果
pytest -k delete    # 只运行名字里含 delete 的测试
```

输出里 `PASSED` 是通过，`FAILED` 会显示期望值和实际值的差异。

> **要点**：pytest 的规则很简单——文件叫 `test_*.py`，函数叫 `test_*`，
> 用 `assert` 判断。就这三条。

> **进阶提示**：上面的测试直接读写真实数据库。规范做法是测试时换一个临时数据库
> （用 `app.dependency_overrides` 替换 `get_db` 依赖）——等你熟练后再研究。

---

## 3. 项目结构的演进

### 阶段一：单文件（学习、原型）

```
project/
└── main.py          # 所有代码
```

### 阶段二：按职责拆分（demo 采用的结构，适合小项目）

```
project/
├── requirements.txt
└── app/
    ├── main.py          # 应用 + 路由
    ├── database.py      # 数据库
    └── schemas.py       # 数据模型
```

### 阶段三：按模块拆分（接口多起来之后）

```
project/
├── requirements.txt
└── app/
    ├── main.py              # 只负责创建 app、挂载路由
    ├── database.py
    ├── routers/             # 每类资源一个路由文件
    │   ├── todos.py         # APIRouter：/todos 相关接口
    │   └── users.py         # APIRouter：/users 相关接口
    ├── schemas/
    │   ├── todo.py
    │   └── user.py
    └── tests/
        ├── test_todos.py
        └── test_users.py
```

阶段三的 main.py 长这样（用第 06 章的 APIRouter）：

```python
from fastapi import FastAPI
from routers import todos, users

app = FastAPI()
app.include_router(todos.router)
app.include_router(users.router)
```

> **要点**：不要过早追求复杂结构。**接口少于 10 个时，阶段二完全够用。**

---

## 4. 部署相关的最基础概念

```bash
# 开发时（--reload 自动重启，只监听本机）
uvicorn main:app --reload

# 局域网内其他设备也能访问（比如用手机测试）
uvicorn main:app --host 0.0.0.0 --port 8000

# 生产环境的最简形态（去掉 --reload，加多个 worker 进程）
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

生产部署还涉及 HTTPS、进程守护、反向代理（Nginx）、容器（Docker）——现阶段了解名词即可。

---

## 5. 下一步学习路线

完成本系列后，你已经具备了 Python 后端的核心能力。建议的进阶顺序：

| 方向 | 学什么 | 为什么 |
|---|---|---|
| **ORM** | SQLAlchemy（或 SQLModel） | 用 Python 类代替手写 SQL，是业界主流做法；SQLModel 由 FastAPI 作者开发，和 Pydantic 无缝衔接 |
| **数据库迁移** | Alembic | 表结构变更的版本管理（生产环境不能随便删库重建） |
| **用户认证** | OAuth2 + JWT | 几乎所有真实应用都需要登录；FastAPI 官方教程有完整章节 |
| **异步深入** | async/await、异步数据库驱动 | 高并发场景的必备 |
| **更大的数据库** | PostgreSQL | SQLite 适合学习和小工具，多用户生产应用一般用 PostgreSQL |
| **容器化** | Docker | 部署的行业标准 |

推荐资源：

- FastAPI 官方教程（有中文版，质量极高）：<https://fastapi.tiangolo.com/zh/tutorial/>
- SQLite 官方文档：<https://www.sqlite.org/docs.html>
- Pydantic 文档：<https://docs.pydantic.dev/>

---

## 小练习

1. 给 demo 项目的 `test_main.py` 补一个测试：`PUT /todos/{id}` 部分更新后，未更新的字段保持不变。
2. 把 demo 的路由拆到 `routers/todos.py` 里（用 APIRouter），确认 /docs 里接口不变、测试仍然通过。
3. （综合挑战）从零写一个 `notes` API：字段 `id / content / created_at`，五个 CRUD 接口 + 4 个测试，全程不看 demo 代码。

> 🎉 完成这个挑战，说明你已经真正掌握了 FastAPI + SQLite 后端开发！
> 回到 [README](../README.md) 查看如何把这些能力用到你自己的项目上。
