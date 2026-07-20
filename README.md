# AI 全栈学习手册

![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-blue)

为 0 基础全栈学习者准备的一套「学习 + 速查 + 实践」系统，覆盖 Python 后端开发核心：
**Python 基础、Git、日志与调试、FastAPI、SQLite、配置与工程化、部署**，以及进阶选修的 **AI Agent 开发**。

> 🌐 **在线阅读**：本项目是一个 VitePress 文档站，push 到 GitHub 后自动部署（见文末「网站开发与部署」）。

> 为了清空 Fable5 额度 >v<

## 三种使用方式

| 场景 | 用什么 | 怎么用 |
|---|---|---|
| 📖 **系统学习** | [在线教程](https://syonling.github.io/AI_Full_Stack_Learning_Handbook/) 或 [docs/](docs/) 全部 25 章文档 | 按下面的路线顺序阅读，每章末尾有小练习 |
| 🔍 **日常速查** | 网站导航栏 **Code Search**（即 [handbook.html](handbook.html)，本地也可双击打开） | 搜索关键词（中英文都行），代码一键复制 |
| 🛠 **动手实践** | [demo/](demo/) 可运行项目 | 按 [demo/README.md](demo/README.md) 的步骤跑起来，边学边改 |

## 推荐学习路线

```
基础工具         后端主线                        工程化落地
─────────       ─────────────────────────      ─────────────────
01 Python  ──▶  04 FastAPI 入门                08 配置与环境变量
02 Git          05 SQLite 基础          ──▶    09 FastAPI 工程化
03 日志与调试     06 FastAPI 进阶                10 测试与结构
                07 整合实战（跑 demo！）          11 部署入门
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
| 13 | [HTML 基础](docs/13-html-basics.md) | 文档骨架、常用标签、语义化、表单 | 2~3 小时 |
| 14 | [CSS 基础](docs/14-css-basics.md) | 选择器、盒模型、Flex/Grid、响应式 | 3~4 小时 |
| 15 | [JavaScript 基础](docs/15-javascript-basics.md) | 变量函数、数组对象、DOM、事件（Python 对照讲解） | 3~4 小时 |
| 16 | [JS 网络与联调](docs/16-js-network-and-integration.md) | fetch、async/await、给 Todo API 写完整前端（与 demo/frontend 对应）★ | 4~5 小时 |
| 17 | [Vue 3 入门](docs/17-vue-basics.md) | 响应式、指令、用 Vue 重写 Todo 页面 | 4~5 小时 |
| 18 | [前端工程组织](docs/18-frontend-engineering.md) | 文件夹分层、CSS 设计令牌、BEM、JS 模块化（含 Vue 对照） | 3~4 小时 |
| 19 | [设计美学：Apple 风格](docs/19-apple-design.md) | HIG 三原则、8pt 留白、毛玻璃、Apple 风换肤实战 | 3~4 小时 |
| 20 | [后端代码组织](docs/20-backend-engineering.md) | 分层、包结构、循环导入、service 拆分时机（属「工程化落地」组，学完 10 章即可读） | 3~4 小时 |
| 27 | [用户登录与身份认证](docs/27-user-authentication.md) | 密码哈希、JWT、注册/登录接口、保护路由、前端令牌配合（属「工程化落地」组，排在 20 章之后）| 4~5 小时 |
| 21 | [音频应用总览与选型](docs/21-audio-overview.md) | 音频零基础速成、架构、外键与 JOIN、选型总表 🎧 项目实践开篇 | 2~3 小时 |
| 22 | [音频播放与播放器](docs/22-audio-playback.md) | audio 标签、Range 请求、自动播放策略、自定义播放器、波形 | 3~4 小时 |
| 23 | [素材入库：上传与录音](docs/23-audio-upload-recording.md) | FormData 上传、uuid 安全命名、mutagen、MediaRecorder 录音 | 4~5 小时 |
| 24 | [AI 语音合成](docs/24-ai-voice-synthesis.md) | 适配器模式、edge-tts 替身、AI API 插槽、202+轮询 | 3~4 小时 |
| 25 | [时间轴编辑器](docs/25-audio-timeline.md) | 像素⇄秒坐标系、Pointer 拖拽、保存加载、串播调度器 🎓 毕业项目 | 6~8 小时 |
| 26 | [终端命令速查与实战](docs/26-terminal-cheatsheet.md) | 附录：文件/进程/端口/管道组合拳、sqlite3 进阶（备份/导出）、危险命令清单 | 按需查阅 |

> 📐 编号规则说明：文件编号是**永久 ID**（只增不改）。后插入的章节按内容归入对应分组、排在组末保持编号升序，章内标注建议阅读位置。

> 🎨 前端章节（13~17）可与后端并行学习：HTML/CSS 无前置依赖；16 章需要 demo 后端能跑（07 章）；17 章需先完成 16 章。

> 💡 学习方法建议：**每章边读边敲代码**（不要复制粘贴）；从 02 章开始每章练习完成后 `git commit` 一次；
> 读完 07 章一定把 [demo/](demo/) 完整跑一遍，08、09 章会带你解锁 demo 里的"生产四件套"。

## 学完之后：毕业项目路线

1. **热身**（16 章终极练习）：从零实现「Audio Book 雏形」——`POST /story` 存故事、`GET /story` 查列表，配一个最简前端页面（13 章第 6 节的原型）
2. **正餐**（21~25 章）：跟着「项目实践」把它长成完整的音频工作台——上传、录音、AI 合成、时间轴编排
3. **上桌**：用 02 章的 Git 管理它、11 章的方式部署它，做成你自己的产品

这就是「学以致用」的完整路线 🎉

## 目录结构

```
learning_from_claude/
├── README.md            ← 你在这里
├── handbook.html        ← 交互式速查手册（210+ 条目，可搜索）
├── docs/                ← 25 章深度文档 + VitePress 站点配置
│   ├── 01~03  基础工具（Python / Git / 日志与调试）
│   ├── 04~07  后端主线（FastAPI / SQLite / 整合实战）
│   ├── 08~11、20  工程化落地（配置 / 工程化 / 测试 / 部署 / 代码组织）
│   ├── 12     AI Agent（进阶选修）
│   ├── 13~19  前端开发（HTML / CSS / JS / Vue / 工程组织 / Apple 设计）
│   └── 21~25  项目实践：音频应用（完整清单见上方路线表）
└── demo/                ← 可运行的 Todo CRUD API（带生产四件套）
    ├── README.md        ← 运行步骤
    ├── requirements.txt
    ├── .env.example     ← 配置模板（复制为 .env 使用）
    ├── app/
    │   ├── main.py      ← 路由 + 日志/中间件/异常兜底/lifespan
    │   ├── config.py    ← pydantic-settings 配置
    │   ├── database.py
    │   └── schemas.py
    └── frontend/        ← 原生 JS 前端页面（对应 16 章，直接双击打开）
        ├── index.html   ← 结构（13 章）
        ├── style.css    ← 样式（14 章）
        └── app.js       ← 行为：fetch 调用 Todo API（15/16 章）
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


## License

CC BY-NC 4.0 (Non-Commercial Use)
