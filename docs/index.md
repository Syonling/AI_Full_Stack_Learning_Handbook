---
layout: home

hero:
  name: AI 全栈学习手册
  text: FastAPI · SQLite · Python 后端 · AI Agent
  tagline: 为 0 基础学习者准备的「学习 + 速查 + 实践」系统，像读一本书一样从零到部署
  image:
    src: /logo.svg
    alt: AI 全栈学习手册
  actions:
    - theme: brand
      text: 开始学习 →
      link: /01-python-backend-basics
    - theme: alt
      text: Code Search 速查手册
      link: /handbook.html
      target: _blank

features:
  - icon: 📖
    title: 系统学习
    details: 十二章深度教程，编号即学习顺序。每章包含学习目标、完整代码示例、常见错误排查表和小练习。
    link: /01-python-backend-basics
    linkText: 从第 01 章开始
  - icon: 🔍
    title: 日常速查
    details: 140+ 条速查卡片，覆盖 Python / FastAPI / SQLite / Git / 日志 / 部署 / AI Agent，支持中英文关键词搜索、代码一键复制。
    link: /handbook.html
    linkText: 打开 Code Search
    target: _blank
  - icon: 🛠
    title: 动手实践
    details: 配套可运行的 Todo CRUD API（demo/ 目录），带日志、异常兜底、.env 配置等"生产四件套"，与教程逐行对应。
    link: /07-fastapi-sqlite-crud
    linkText: 查看整合实战
---

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
| 01 | [Python 后端基础](/01-python-backend-basics) | venv、类型注解、字典列表、异常、import | 2~3 小时 |
| 02 | [Git 版本控制](/02-git-basics) | init/add/commit、分支、撤销、GitHub | 2~3 小时 |
| 03 | [日志与调试](/03-logging-and-debugging) | logging 级别/文件/轮转、读 traceback、断点调试 | 3~4 小时 |
| 04 | [FastAPI 入门](/04-fastapi-basics) | 路由、路径/查询参数、请求体、/docs | 3~4 小时 |
| 05 | [SQLite 基础](/05-sqlite-basics) | SQL 增删改查、参数化查询、事务 | 3~4 小时 |
| 06 | [FastAPI 进阶](/06-fastapi-advanced) | Pydantic 校验、错误处理、CORS、Depends | 3~4 小时 |
| 07 | [整合实战](/07-fastapi-sqlite-crud) | 完整 CRUD API（与 demo 代码逐行对应） | 4~5 小时 |
| 08 | [配置与环境变量](/08-config-and-env) | .env、pydantic-settings、密钥安全 | 2~3 小时 |
| 09 | [FastAPI 工程化](/09-fastapi-engineering) | 请求日志中间件、全局异常兜底、lifespan、后台任务 | 3~4 小时 |
| 10 | [测试与结构](/10-testing-and-structure) | curl、pytest、项目结构、进阶路线 | 2~3 小时 |
| 11 | [部署入门](/11-deployment) | 生产运行、进程守护、Docker、上线检查清单 | 3~4 小时 |
| 12 | [AI Agent 开发](/12-ai-agents) | Agent 原理、Tool Use、MCP、Skill、LangChain、LangGraph | 4~6 小时 |
| 13 | [HTML 基础](/13-html-basics) | 文档骨架、常用标签、语义化、表单 | 2~3 小时 |
| 14 | [CSS 基础](/14-css-basics) | 选择器、盒模型、Flex/Grid、响应式 | 3~4 小时 |
| 15 | [JavaScript 基础](/15-javascript-basics) | 变量函数、数组对象、DOM、事件（Python 对照讲解） | 3~4 小时 |
| 16 | [JS 网络与联调](/16-js-network-and-integration) | fetch、async/await、给 Todo API 写完整前端 ★ | 4~5 小时 |
| 17 | [Vue 3 入门](/17-vue-basics) | 响应式、指令、用 Vue 重写 Todo 页面 | 4~5 小时 |
| 18 | [前端工程组织](/18-frontend-engineering) | 文件夹分层、CSS 设计令牌、BEM 命名、JS 模块化（含 Vue 项目对照） | 3~4 小时 |
| 19 | [设计美学：Apple 风格](/19-apple-design) | HIG 三原则、8pt 留白、字阶、毛玻璃、Apple 风换肤实战 | 3~4 小时 |
| 20 | [后端代码组织](/20-backend-engineering) | 分层思想、包结构、循环导入、service 层拆分时机（属「工程化落地」组，学完 10 章即可读） | 3~4 小时 |
| 21 | [音频应用总览与选型](/21-audio-overview) | 音频零基础速成、架构设计、外键与 JOIN、选型总表 🎧 | 2~3 小时 |
| 22 | [音频播放与播放器](/22-audio-playback) | audio 标签、Range 请求、自动播放策略、自定义播放器、波形 | 3~4 小时 |
| 23 | [素材入库：上传与录音](/23-audio-upload-recording) | FormData 上传、uuid 安全命名、mutagen、MediaRecorder 录音 | 4~5 小时 |
| 24 | [AI 语音合成](/24-ai-voice-synthesis) | 适配器模式、edge-tts 免费替身、AI API 插槽、202+轮询 | 3~4 小时 |
| 25 | [时间轴编辑器](/25-audio-timeline) | 像素⇄秒坐标系、Pointer 拖拽、保存加载、串播调度器 🎓 毕业项目 | 6~8 小时 |

> 🎨 **前端章节（13~17）无需按总编号顺序等待**——HTML/CSS 没有任何前置依赖，可与后端章节并行学习；
> 16 章需要后端 demo 能跑起来（07 章），17 章需要先完成 16 章。

::: tip 学习方法建议
**每章边读边敲代码**（不要复制粘贴）；从 02 章开始每章练习完成后 `git commit` 一次；
读完 07 章一定把仓库里的 `demo/` 项目完整跑一遍，08、09 章会带你解锁 demo 里的"生产四件套"。
:::

## 三种使用方式

| 场景 | 用什么 | 怎么用 |
|---|---|---|
| 📖 **系统学习** | 左侧目录十二章教程 | 按编号顺序阅读，每章末尾有小练习 |
| 🔍 **日常速查** | 顶部导航 **Code Search** | 搜索中英文关键词，代码一键复制 |
| 🛠 **动手实践** | 仓库中的 `demo/` 目录 | 按 demo/README.md 的步骤跑起来，边学边改 |

## 学完之后

学完本系列，你将具备独立完成一个「前端 + FastAPI 后端 + SQLite 数据库」全栈应用，
并把它用 Git 管理、用 Docker 部署上线的完整能力——再加上第 12 章的 AI Agent 知识地图，
「后端 API + AI 能力」正是当下最有价值的全栈技能组合之一 🎉
