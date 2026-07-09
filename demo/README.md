# Todo API Demo —— 可运行的练习项目

FastAPI + SQLite 的完整 CRUD 示例（CRUD 部分与 [docs/07 章](../docs/07-fastapi-sqlite-crud.md) 逐行对应），
并带有"生产四件套"：日志、请求中间件、全局异常兜底、.env 配置（对应 [docs/03](../docs/03-logging-and-debugging.md)、[docs/08](../docs/08-config-and-env.md)、[docs/09](../docs/09-fastapi-engineering.md) 章）。

## 文件说明

| 文件 | 职责 | 对应章节 |
|---|---|---|
| [app/main.py](app/main.py) | FastAPI 应用 + CRUD 路由 + 日志/中间件/异常兜底/lifespan | 07 / 03 / 09 |
| [app/database.py](app/database.py) | SQLite 连接、建表、依赖函数 | 05 / 07 |
| [app/schemas.py](app/schemas.py) | Pydantic 请求/响应模型 | 06 / 07 |
| [app/config.py](app/config.py) | 配置读取（pydantic-settings + .env） | 08 |
| .env.example | 配置模板（复制为 .env 使用；.env 不进 Git） | 08 |
| requirements.txt | 依赖清单（sqlite3 是 Python 标准库，无需安装） | — |
| todos.db | 运行后自动生成的数据库文件 | — |

## 第一次运行（完整步骤）

```bash
# 1. 进入 demo 文件夹
cd demo

# 2. 创建并激活虚拟环境（只需做一次）
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖（只需做一次）
pip install -r requirements.txt

# 4. 进入 app 目录并启动服务器
cd app
uvicorn main:app --reload
```

看到 `Uvicorn running on http://127.0.0.1:8000` 就成功了。

## 之后每次运行

```bash
cd demo
source .venv/bin/activate
cd app
uvicorn main:app --reload
```

按 `Ctrl + C` 停止服务器。

## 测试接口

**方式一（推荐）**：浏览器打开 <http://127.0.0.1:8000/docs>，
每个接口点 **Try it out → Execute** 直接测试。

**方式二**：另开一个终端用 curl：

```bash
# 新建一条待办
curl -s -X POST "http://127.0.0.1:8000/todos" \
  -H "Content-Type: application/json" \
  -d '{"title": "my first todo"}'

# 查看全部
curl -s "http://127.0.0.1:8000/todos" | python3 -m json.tool

# 标记 id=1 为已完成（部分更新）
curl -s -X PUT "http://127.0.0.1:8000/todos/1" \
  -H "Content-Type: application/json" \
  -d '{"done": true}'

# 只看已完成的
curl -s "http://127.0.0.1:8000/todos?done=true"

# 删除 id=1
curl -s -i -X DELETE "http://127.0.0.1:8000/todos/1"
```

## 验证"数据真的保存了"

新建几条待办后，`Ctrl + C` 停掉服务器，再重新启动，
`GET /todos` —— 数据还在（都存在 `todos.db` 文件里）。

想重置所有数据：停掉服务器，删除 `demo/todos.db`，重启即可。

## 常见问题

| 问题 | 解决 |
|---|---|
| `command not found: uvicorn` | 虚拟环境没激活：`source .venv/bin/activate` |
| `Could not import module "main"` | 要在 `app/` 目录下运行 uvicorn |
| 改代码没生效 | 启动命令要带 `--reload` |
| 端口被占用 | 换端口：`uvicorn main:app --reload --port 8001` |
