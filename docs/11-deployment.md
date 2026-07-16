# 11 · 部署入门

> 本章目标：理解"让别人也能访问你的 API"需要什么，掌握生产运行方式，初识 Docker。
> 预计学习时间：3~4 小时。概念为主 + 可跟做的 Docker 示例。

---

## 学习目标

1. 分清开发模式和生产模式的运行差异
2. 会用正确的参数在"生产姿态"下启动 uvicorn
3. 理解进程守护（服务怎么做到 7×24 不断）
4. 写出第一个 Dockerfile 并跑起来
5. 知道 Nginx 反向代理和 HTTPS 在架构里的位置
6. 有一份上线前检查清单

---

## 1. 开发模式 vs 生产模式

```bash
# 开发（你一直在用的）
uvicorn main:app --reload
#   --reload: 改代码自动重启 —— 方便，但耗资源且不稳定，生产禁用
#   默认只监听 127.0.0.1 —— 只有本机能访问

# 生产
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
#   --host 0.0.0.0: 监听所有网卡，外部才能访问
#   --workers 4:    启动 4 个进程并行处理请求（一般设为 CPU 核数）
#   没有 --reload
```

| 差异点 | 开发 | 生产 |
|---|---|---|
| `--reload` | ✅ | ❌ 禁用 |
| 监听地址 | 127.0.0.1（仅本机） | 0.0.0.0（配合防火墙/代理） |
| workers | 1 | CPU 核数左右 |
| 日志级别 | DEBUG | INFO / WARNING（第 08 章的 .env 控制） |
| CORS | `*` 全开 | 具体域名 |

> **要点**：`--host 0.0.0.0` 后，同一局域网的设备（比如你的手机）就能通过
> `http://你电脑的IP:8000` 访问——这也是联调前端的常用技巧。

⚠️ **workers > 1 与 SQLite**：多个进程同时写一个 SQLite 文件容易碰到 `database is locked`。
学习项目用 `--workers 1` 完全够；真要高并发，就该换 PostgreSQL 了（第 10 章的进阶路线）。

---

## 2. 进程守护：服务怎么 7×24 跑

直接在终端跑 `uvicorn`，关掉终端服务就死了。生产需要一个"保姆"进程：
**开机自启、崩溃自动拉起、统一管理日志**。Linux 服务器上的标准答案是 **systemd**：

```ini
# /etc/systemd/system/todo-api.service（概念示例，部署到 Linux 服务器时用）
[Unit]
Description=Todo API
After=network.target

[Service]
User=appuser
WorkingDirectory=/srv/todo-api/app
EnvironmentFile=/srv/todo-api/.env
ExecStart=/srv/todo-api/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always                  # ← 崩溃自动重启

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl start todo-api      # 启动
sudo systemctl enable todo-api     # 开机自启
sudo systemctl status todo-api     # 查看状态
journalctl -u todo-api -f          # 实时看日志
```

现阶段**理解概念即可**：生产服务永远由守护系统管理，而不是一个开着的终端窗口。

---

## 3. Docker：把环境打包带走

### 3.1 解决什么问题？

"在我电脑上能跑"——因为你的电脑有对的 Python 版本、装好的依赖、对的系统库。
**Docker 把"代码 + 依赖 + 运行环境"打包成一个镜像（image）**，在任何装了 Docker 的机器上行为完全一致。

| 概念 | 类比 |
|---|---|
| Dockerfile | 菜谱：怎么一步步做出环境 |
| 镜像 image | 做好的冷冻便当：随时可复制、分发 |
| 容器 container | 加热开吃的那一份：镜像的运行实例 |

### 3.2 给 demo 写一个 Dockerfile

在 `demo/` 目录下创建 `Dockerfile`（无扩展名）：

```dockerfile
# 基础镜像：官方精简版 Python
FROM python:3.12-slim

# 容器内的工作目录
WORKDIR /code

# 先复制依赖清单并安装——利用构建缓存：依赖没变就不用重装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再复制应用代码
COPY app/ ./app/

# 声明服务端口
EXPOSE 8000

# 启动命令（注意：容器里必须监听 0.0.0.0）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

再加一个 `.dockerignore`（同 .gitignore 的思路，别把垃圾打进镜像）：

```
.venv/
__pycache__/
*.db
.env
```

### 3.3 构建与运行

先安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（macOS 直接下载安装）。

```bash
cd demo
docker build -t todo-api .          # 构建镜像，命名为 todo-api
docker run -p 8000:8000 todo-api    # 运行：把容器的 8000 映射到本机 8000

# 浏览器打开 http://127.0.0.1:8000/docs —— 和本地跑一模一样！
```

常用管理命令：

```bash
docker ps                  # 查看运行中的容器
docker logs <容器ID>       # 看容器日志
docker stop <容器ID>       # 停止
docker run -d -p 8000:8000 todo-api        # -d 后台运行
docker run -p 8000:8000 --env-file .env todo-api   # 注入配置（第 08 章）
```

> **注意**：容器里写的 SQLite 文件在容器删除时会一起消失。
> 数据要持久化需要挂载卷：`docker run -v $(pwd)/data:/code/data ...`——知道有这回事即可，用到再查。

---

## 4. 全景图：反向代理与 HTTPS

真实部署中，用户不会直接连 uvicorn。标准架构：

```
用户浏览器
   │  https://api.example.com  （443 端口，HTTPS 加密）
   ▼
Nginx（反向代理）             ← 负责：HTTPS 证书、静态文件、限流、
   │  http://127.0.0.1:8000      转发给后端、负载均衡多个 worker
   ▼
uvicorn（你的 FastAPI 应用）   ← 只监听本机，不直接暴露给公网
```

- **反向代理（Nginx / Caddy）**：站在你的应用前面接客，把请求转发进来
- **HTTPS**：给传输加密。证书可用 [Let's Encrypt](https://letsencrypt.org/) 免费签发（Caddy 甚至全自动）

现阶段记住架构图即可。另外，对个人项目来说，**PaaS 平台**（Railway、Render、Fly.io 等）
能把这一整套（HTTPS、守护、日志）都替你管了——连接 GitHub 仓库即可部署，是最省心的第一站。

---

## 5. 上线前检查清单

- [ ] 去掉 `--reload`；workers 按需设置（SQLite 项目保持 1）
- [ ] `LOG_LEVEL` 调到 INFO；日志输出到文件并配置轮转（第 03 章）
- [ ] CORS 从 `*` 收紧到具体前端域名（第 06 章）
- [ ] 所有密钥通过环境变量/.env 注入，仓库里无明文（第 08 章）
- [ ] `.env` 不在镜像和 Git 里；有 `.env.example`
- [ ] 全局异常处理器就位，用户永远看不到堆栈（第 09 章）
- [ ] 数据库文件有备份策略（哪怕是每天 `cp todos.db backup/`）
- [ ] 试过 `docker run` 或 systemd 拉起后，杀掉进程能自动恢复
- [ ] （可选）生产环境关闭 /docs：`FastAPI(docs_url=None, redoc_url=None)`

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 容器跑起来但访问不到 | 应用监听了 127.0.0.1 | 容器内必须 `--host 0.0.0.0` |
| `port is already allocated` | 本机 8000 被占用 | 换映射 `-p 8001:8000` |
| 镜像构建巨慢/巨大 | 没有 .dockerignore，把 .venv 打进去了 | 补 .dockerignore |
| 容器里读不到配置 | .env 没进镜像（这是对的！） | 用 `--env-file .env` 运行时注入 |
| `database is locked` | 多 worker 写 SQLite | workers=1，或换 PostgreSQL |
| 局域网设备访问不了 | 没用 0.0.0.0 / 防火墙拦截 | `--host 0.0.0.0`；检查系统防火墙 |

---

## 小练习

1. 用生产参数（无 reload、host 0.0.0.0）启动 demo，用手机（同 Wi-Fi）访问你电脑 IP 的 /docs。
2. 按 3.2 节给 demo 写 Dockerfile 和 .dockerignore，构建并运行，完成一次完整的 CRUD 操作。
3. 停掉容器再启动一个新容器，观察数据是否还在——理解"容器是一次性的"。
4. 对照第 5 节清单，逐项检查 demo 目前的状态，把不满足的项修掉。

> 下一章：[20 · 后端代码组织](20-backend-engineering.md)——工程化落地的收官。
> 之后是进阶选修 [12 · AI Agent](12-ai-agents.md)、13 章起的前端篇，以及 21 章起的音频项目实践。
