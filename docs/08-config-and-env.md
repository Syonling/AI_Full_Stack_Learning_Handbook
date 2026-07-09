# 08 · 配置管理与环境变量

> 本章目标：把"写死在代码里的配置"抽出来，学会用环境变量和 .env 文件管理配置与密钥。
> 预计学习时间：2~3 小时。需要第 06 章的 Pydantic 知识。demo 项目已按本章方式升级，可对照阅读。

---

## 学习目标

1. 明白为什么配置不能写死在代码里
2. 会读取环境变量（`os.environ`）
3. 会用 `.env` 文件 + `pydantic-settings` 管理配置（推荐方案）
4. 会区分开发 / 生产环境的配置
5. 掌握密钥安全的基本纪律

---

## 1. 问题：配置写死的代价

```python
# ❌ 这些值都"写死"（hardcode）在代码里
DB_PATH = "/Users/xue/dev/todos.db"     # 换台电脑就跑不起来
API_KEY = "sk-ant-abc123..."            # 提交到 GitHub = 全世界都能用你的额度
DEBUG = True                            # 上线忘了改，用户看到报错堆栈
```

**配置**（会随环境变化的值）应该和**代码**（不随环境变化的逻辑）分离：

| 属于配置 | 属于代码 |
|---|---|
| 数据库地址、端口、日志级别 | 路由逻辑、SQL 语句 |
| API key、密码等密钥 | 数据模型、校验规则 |
| 开发/生产模式开关 | 业务规则 |

---

## 2. 环境变量：配置的标准载体

环境变量是操作系统提供的"键值对"，程序启动时读取。这是所有语言、所有部署平台通用的配置方式。

```bash
# 终端里设置（只对当前终端会话有效）
export APP_NAME="Todo API"
export LOG_LEVEL="DEBUG"
```

```python
import os

# 读取。第二个参数是默认值（读不到时用）
app_name = os.environ.get("APP_NAME", "My App")
log_level = os.getenv("LOG_LEVEL", "INFO")        # getenv 是 environ.get 的别名

# 必须存在的配置：读不到就大声失败（比带着错误配置默默运行好）
api_key = os.environ["ANTHROPIC_API_KEY"]         # 不存在则 KeyError
```

> **要点**：环境变量的值**永远是字符串**。`export DEBUG=False` 读出来是 `"False"`，
> 而 `bool("False") == True`（非空字符串都是真）！这类转换坑正是下一节工具要解决的。

---

## 3. .env 文件 + pydantic-settings（推荐方案）

每次开终端都 export 一遍太麻烦。约定做法：把配置写进项目根目录的 **`.env` 文件**：

```bash
# .env —— 键=值，一行一个，不要加空格和引号
APP_NAME=Todo API
LOG_LEVEL=DEBUG
DB_FILENAME=todos.db
```

用 `pydantic-settings` 读取——它和你在第 06 章学的 Pydantic 是同一套体系，
自动完成**读取 + 类型转换 + 校验 + 默认值**：

```bash
pip install pydantic-settings
```

```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 字段名对应环境变量名（不区分大小写）：app_name ← APP_NAME
    app_name: str = "Todo API"          # 有默认值 = 可选配置
    log_level: str = "INFO"
    db_filename: str = "todos.db"
    debug: bool = False                 # "true"/"1"/"yes" 都能正确转成 True！

    model_config = SettingsConfigDict(
        env_file=".env",                # 从 .env 文件读
        env_file_encoding="utf-8",
    )

settings = Settings()    # 创建一次，全项目 import 使用
```

```python
# main.py —— 任何文件里这样用
from config import settings

print(settings.app_name)     # Todo API
print(settings.debug)        # False（真正的 bool，不是字符串！）
```

优先级（高覆盖低）：**真实环境变量 > .env 文件 > 代码里的默认值**。
所以生产服务器上用环境变量注入，本地开发用 .env，互不干扰。

> **要点**：必填配置（如密钥）不要给默认值——`api_key: str`（无默认值）。
> 缺失时启动直接报清晰的 ValidationError，远好过运行到一半才炸。

---

## 4. 开发 / 生产环境分离

同一份代码，不同环境不同配置：

| 配置项 | 开发环境 | 生产环境 |
|---|---|---|
| LOG_LEVEL | DEBUG | INFO 或 WARNING |
| DEBUG | true | false |
| 数据库 | 本地 todos.db | 服务器上的正式库 |
| CORS 允许来源 | `*` | 具体域名 |

实现方式很简单——**每个环境放一份不同的 `.env`**：

```
本地开发机的 .env:    LOG_LEVEL=DEBUG  debug=true
生产服务器的 .env:    LOG_LEVEL=INFO   debug=false
```

`.env` 不进 Git（见下节），所以每台机器保留自己的版本，代码到处都能跑。

---

## 5. 密钥安全纪律（重要！）

API key、数据库密码一旦泄露：轻则被刷爆额度产生账单，重则数据被删。纪律只有四条：

1. **`.env` 必须写进 `.gitignore`**（第 02 章的模板已包含）——密钥永不进版本库
2. **提交一份 `.env.example` 作为模板**（只有键名和假值，让协作者知道要配什么）：

   ```bash
   # .env.example —— 复制为 .env 并填入真实值
   APP_NAME=Todo API
   LOG_LEVEL=INFO
   ANTHROPIC_API_KEY=sk-ant-xxxx-replace-me
   ```

3. **代码和日志里不出现密钥明文**（第 03 章讲过：不进日志；同样不进报错信息、不进注释）
4. **真的泄露了**（比如不小心 push 了）：第一时间去服务商后台**吊销并重新生成**——
   从 Git 历史里删除是不够的，爬虫抓 GitHub 泄露密钥只需几分钟

---

## 6. 对照 demo：本章在真实项目里的样子

demo 项目已按本章升级，结构变成：

```
demo/
├── .env.example         # 配置模板（进 Git）
├── .env                 # 你的本地配置（不进 Git，可自己创建）
└── app/
    ├── config.py        # ★ 本章主角：Settings 类
    ├── main.py          # from config import settings
    ├── database.py      # 数据库文件名从 settings 读取
    └── schemas.py
```

打开 [demo/app/config.py](../demo/app/config.py) 对照本节代码；
试着建一个 `demo/.env` 写入 `LOG_LEVEL=DEBUG`，重启服务观察日志变多了。

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 改了 .env 不生效 | 服务没重启 / .env 路径不对 | 重启；确认 .env 位置与 `env_file` 配置一致 |
| `ValidationError: field required` | 必填配置没提供 | 在 .env 或环境变量里补上（这是好事——早发现） |
| bool 配置永远是 True | 用了 `os.environ` + `bool()` 手动转换 | 用 pydantic-settings，它认识 "false"/"0" |
| .env 里的值带上了引号 | 写成 `KEY="value"` | 直接 `KEY=value`，不加引号 |
| 密钥被提交进了 Git | .gitignore 加晚了 | 立即吊销重发密钥；`git rm --cached .env` |
| 生产读到了开发配置 | 两台机器共用了 .env | 每台机器独立维护自己的 .env |

---

## 小练习

1. 给 demo 创建 `.env`，把 `LOG_LEVEL` 改成 `DEBUG`、`APP_NAME` 改成你喜欢的名字，
   重启后在 /docs 页面标题和日志输出里验证生效。
2. 给 `Settings` 加一个必填字段 `secret_token: str`（无默认值），
   观察不配置时启动报什么错，然后在 .env 里补上。
3. 检查你自己的练习仓库：`.gitignore` 是否覆盖了 `.env`？有没有写 `.env.example`？
4. （思考题）为什么 `.env.example` 应该进 Git，而 `.env` 不应该？

> 下一章：[09 · FastAPI 工程化](09-fastapi-engineering.md) —— 中间件、全局异常处理、生命周期，让 API 有"生产味"。
