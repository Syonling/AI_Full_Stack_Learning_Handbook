# AI 全栈学习手册

为 0 基础全栈学习者准备的一套「学习 + 速查 + 实践」系统，覆盖 Python 后端开发核心：
**Python 基础、Git、日志与调试、FastAPI、SQLite、配置与工程化、部署**，以及进阶选修的 **AI Agent 开发**。

> 🌐 **在线阅读**：本项目是一个 VitePress 文档站，push 到 GitHub 后自动部署（见文末「网站开发与部署」）。
> 部署后访问 `https://<你的用户名>.github.io/<仓库名>/`。

## 三种使用方式

| 场景 | 用什么 | 怎么用 |
|---|---|---|
| 📖 **系统学习** | [在线教程](https://syonling.github.io/AI_Full_Stack_Learning_Handbook/) 或 [docs/](docs/) 十二章文档 | 按下面的路线顺序阅读，每章末尾有小练习 |
| 🔍 **日常速查** | 网站导航栏 **Code Search**（即 [handbook.html](handbook.html)，本地也可双击打开） | 搜索关键词（中英文都行），代码一键复制 |
| 🛠 **动手实践** | [demo/](demo/) 可运行项目 | 按 [demo/README.md](demo/README.md) 的步骤跑起来，边学边改 |

## 推荐学习路线

```
基础工具         后端主线                        工程化落地
─────────       ─────────────────────────      ─────────────────
01 Python  ──▶  04 FastAPI 入门                08 配置与环境变量
02 Git          05 SQLite 基础          ──▶    09 FastAPI 工程化
03 日志与调试    06 FastAPI 进阶                10 测试与结构
                07 整合实战（跑 demo！）        11 部署入门
                                                    │
                                                    ▼
                                          12 AI Agent 开发（进阶选修）
```

| 顺序 | 章节 | 内容 | 预计时间 |
|---|---|---|---|
| 01 | [Python 后端基础](docs/01-python-backend-basics.md) | venv、类型注解、字典列表、异常、import | 2~3 小时 |
| 02 | [Git 版本控制](docs/02-git-basics.md) | init/add/commit、分支、撤销、GitHub | 2~3 小时 |
| 03 | [日志与调试](docs/03-logging-and-debugging.md) | logging 级别/文件/轮转、读 traceback、断点调试 | 3~4 小时 |
| 04 | [FastAPI 入门](docs/04-fastapi-basics.md) | 路由、路径/查询参数、请求体、/docs | 3~4 小时 |
| 05 | [SQLite 基础](docs/05-sqlite-basics.md) | SQL 增删改查、参数化查询、事务 | 3~4 小时 |
| 06 | [FastAPI 进阶](docs/06-fastapi-advanced.md) | Pydantic 校验、错误处理、CORS、Depends | 3~4 小时 |
| 07 | [整合实战](docs/07-fastapi-sqlite-crud.md) | 完整 CRUD API（与 demo 代码逐行对应） | 4~5 小时 |
| 08 | [配置与环境变量](docs/08-config-and-env.md) | .env、pydantic-settings、密钥安全 | 2~3 小时 |
| 09 | [FastAPI 工程化](docs/09-fastapi-engineering.md) | 请求日志中间件、全局异常兜底、lifespan、后台任务 | 3~4 小时 |
| 10 | [测试与结构](docs/10-testing-and-structure.md) | curl、pytest、项目结构、进阶路线 | 2~3 小时 |
| 11 | [部署入门](docs/11-deployment.md) | 生产运行、进程守护、Docker、上线检查清单 | 3~4 小时 |
| 12 | [AI Agent 开发](docs/12-ai-agents.md) | Agent 原理、Tool Use、MCP、Skill、LangChain、LangGraph（纯教学，无 demo） | 4~6 小时 |

> 💡 学习方法建议：**每章边读边敲代码**（不要复制粘贴）；从 02 章开始每章练习完成后 `git commit` 一次；
> 读完 07 章一定把 [demo/](demo/) 完整跑一遍，08、09 章会带你解锁 demo 里的"生产四件套"。

## 学完之后：应用到你的 Audio Book 项目

你的 [Frontend/main.html](../Frontend/main.html) 已经会调用 `POST /story` 和 `GET /story`。学完本系列后，你完全有能力在 [Backend/main.py](../Backend/main.py) 里实现它：

1. 参照 demo 的结构搭建 Backend（含 config.py、日志、异常兜底）
2. 建一张 `stories` 表（字段：`id`、`text`）
3. 实现 `POST /story`（接收 `{"text": ...}`，存入 SQLite，返回消息）
4. 实现 `GET /story`（返回所有故事的列表 `[{"text": ...}, ...]`，正好匹配前端的 `data.map(item => item.text)`）
5. 记得配置 CORS（或用 StaticFiles 让后端直接托管前端页面）
6. 用 02 章的 Git 管理它、11 章的方式部署它

这就是「学以致用」的第一个里程碑 🎉

## 目录结构

```
learning_from_claude/
├── README.md            ← 你在这里
├── handbook.html        ← 交互式速查手册（140+ 条目，可搜索）
├── docs/                ← 十二章深度文档（编号即学习顺序）
│   ├── 01-python-backend-basics.md
│   ├── 02-git-basics.md
│   ├── 03-logging-and-debugging.md
│   ├── 04-fastapi-basics.md
│   ├── 05-sqlite-basics.md
│   ├── 06-fastapi-advanced.md
│   ├── 07-fastapi-sqlite-crud.md
│   ├── 08-config-and-env.md
│   ├── 09-fastapi-engineering.md
│   ├── 10-testing-and-structure.md
│   ├── 11-deployment.md
│   └── 12-ai-agents.md      ← Agent / MCP / Skill / LangChain / LangGraph
└── demo/                ← 可运行的 Todo CRUD API（带生产四件套）
    ├── README.md        ← 运行步骤
    ├── requirements.txt
    ├── .env.example     ← 配置模板（复制为 .env 使用）
    └── app/
        ├── main.py      ← 路由 + 日志/中间件/异常兜底/lifespan
        ├── config.py    ← pydantic-settings 配置
        ├── database.py
        └── schemas.py
```

## 网站开发与部署（VitePress）

```bash
npm install            # 首次
npm run docs:dev       # 本地开发，http://localhost:5173
npm run docs:build     # 构建（产物在 docs/.vitepress/dist）
npm run docs:preview   # 本地预览构建结果
```

**发布到 GitHub Pages（只需配置一次）：**

1. 以本目录为仓库根 `git init`，推送到 GitHub
2. 仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**
3. 之后每次 `git push`，[.github/workflows/deploy.yml](.github/workflows/deploy.yml) 自动构建并部署
