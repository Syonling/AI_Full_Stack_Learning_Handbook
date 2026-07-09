# 03 · 日志与调试

> 本章目标：掌握两项"排查问题"的核心能力——用 logging 让程序留下运行记录，用调试器和报错堆栈定位 bug。
> 预计学习时间：3~4 小时。只需第 01 章的知识；FastAPI 中的日志集成在第 09 章。

---

## 学习目标

1. 明白为什么正式项目**不用 `print` 而用 `logging`**
2. 掌握日志级别（DEBUG / INFO / WARNING / ERROR / CRITICAL）
3. 会配置日志：格式、输出到文件、按大小轮转
4. 会正确记录异常（含完整堆栈）
5. 会读懂 Python 报错堆栈（traceback）
6. 会用 `breakpoint()` 和 VSCode 断点调试

---

## 1. 为什么不用 print？

`print` 调试的问题：

| print 的问题 | logging 的解决方式 |
|---|---|
| 上线前要手动删掉，删漏了污染输出 | 调整日志级别即可全局开关，代码不用动 |
| 没有时间、位置信息 | 自动带时间戳、模块名、级别 |
| 只能输出到屏幕 | 可同时输出到屏幕 + 文件，文件还能自动轮转 |
| 无法区分"正常信息"和"错误" | 五个级别，可分别处理 |
| 服务器上程序崩了，什么线索都没留下 | 日志文件就是"黑匣子" |

> **经验法则**：临时看一眼变量可以用 print（看完就删）；
> 任何会运行超过一天的程序，一律用 logging。

---

## 2. logging 快速上手

```python
import logging

# 一行配置（放在程序入口，只配置一次）
logging.basicConfig(
    level=logging.INFO,      # 低于 INFO 的（即 DEBUG）不输出
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)    # 用模块名创建 logger（惯用写法）

logger.debug("detail for developers")       # 不会输出（级别低于 INFO）
logger.info("server started on port 8000")  # 会输出
logger.warning("disk usage at 85%")
logger.error("failed to connect to database")
```

输出长这样：

```
2026-07-09 15:30:12,345 INFO __main__ - server started on port 8000
2026-07-09 15:30:12,346 WARNING __main__ - disk usage at 85%
```

### 五个级别的使用场景

| 级别 | 什么时候用 | 例子 |
|---|---|---|
| `DEBUG` | 开发时的细节信息 | "查询参数 = {...}" |
| `INFO` | 正常的关键事件 | "服务启动"、"用户 5 创建了待办" |
| `WARNING` | 不正常但还能继续 | "重试第 2 次"、"配置缺失，使用默认值" |
| `ERROR` | 某个操作失败了 | "写入数据库失败" |
| `CRITICAL` | 整个程序快不行了 | "磁盘满，无法继续服务" |

`level=logging.INFO` 的含义：**输出 INFO 及以上**，屏蔽 DEBUG。
开发时设 DEBUG（信息全开），上线设 INFO 或 WARNING（只留重要的）。

> **要点**：`getLogger(__name__)` 让每条日志自动带上模块名——
> 多文件项目里一眼看出这条日志是哪个文件打的。不要到处 `print`，也不要到处 `basicConfig`（入口配一次）。

---

## 3. 输出到文件 + 自动轮转

日志写进文件才能事后排查。但文件会越写越大，要用**轮转（rotation）**限制体积：

```python
import logging
from logging.handlers import RotatingFileHandler

# handler 决定"日志去哪"；formatter 决定"长什么样"
file_handler = RotatingFileHandler(
    "app.log",
    maxBytes=1_000_000,      # 单个文件最大 1MB
    backupCount=3,           # 最多保留 3 个旧文件（app.log.1 / .2 / .3）
    encoding="utf-8",
)
console_handler = logging.StreamHandler()     # 同时输出到屏幕

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    handlers=[file_handler, console_handler],  # 一条日志，两个去处
)

logger = logging.getLogger(__name__)
logger.info("this line goes to both screen and app.log")
```

三件套关系（理解 logging 体系的钥匙）：

```
logger（你调用的入口）
  └─▶ handler（去哪：屏幕 / 文件 / 网络……可以挂多个）
        └─▶ formatter（长什么样：时间、级别、消息的排版）
```

常用格式占位符：`%(asctime)s` 时间、`%(levelname)s` 级别、`%(name)s` 模块、
`%(message)s` 内容、`%(lineno)d` 行号。

---

## 4. 正确记录异常

新手最常见的错误写法——只记了错误信息，丢了**最有价值的堆栈**：

```python
# ❌ 只知道"出错了"，不知道在哪一行、怎么走到那的
try:
    risky_operation()
except Exception as e:
    logger.error(f"something failed: {e}")

# ✅ logger.exception 自动附带完整 traceback（只能在 except 块里用）
try:
    risky_operation()
except Exception:
    logger.exception("risky_operation failed")

# ✅ 等价写法：exc_info=True
logger.error("risky_operation failed", exc_info=True)
```

### 日志里绝不能出现的东西

```python
# ❌ 密码、API key、token、身份证号……日志文件往往权限宽松、会被上传
logger.info(f"user login: password={password}")
logger.debug(f"calling api with key={api_key}")

# ✅ 记录"发生了什么"，不记录敏感值本身
logger.info("user %s login success", username)
```

> **要点**：日志参数推荐用 `logger.info("user %s created", name)` 的占位符写法
> 而不是 f-string——级别被屏蔽时字符串就不会白白拼接（还能防注入混淆）。养成习惯即可，不必纠结。

---

## 5. 读懂报错堆栈（traceback）

调试的第一步不是加 print，是**把报错读完**。规则只有一条：**从下往上读**。

```
Traceback (most recent call last):
  File "main.py", line 10, in <module>
    result = process_order(order)              ← ③ 入口：谁发起的
  File "main.py", line 6, in process_order
    total = calc_total(order["items"])         ← ② 中间：经过了谁
  File "main.py", line 2, in calc_total
    return sum(item["price"] for item in items)
KeyError: 'price'                              ← ① 先看这里：错误类型 + 信息
```

三步走：

1. **最后一行**：错误类型（`KeyError: 'price'`）——字典里没有 `price` 这个键
2. **往上找到自己写的代码**中最靠下的一行——`calc_total` 第 2 行就是出错现场
3. 思考数据从哪来：`items` 里有个元素没有 `price` 键 → 检查上游数据

常见错误类型速记：

| 错误 | 大概率原因 |
|---|---|
| `KeyError` / `IndexError` | 字典没这个键 / 列表越界 |
| `TypeError: 'NoneType' ...` | 某个函数返回了 None 你没检查 |
| `AttributeError` | 对象没有这个方法/属性（常见于拼写错误） |
| `ImportError / ModuleNotFoundError` | 没装包 / 没激活 venv / 文件名冲突 |
| `ValueError` | 类型对但值不合法（如 `int("abc")`） |

---

## 6. 断点调试：比 print 高效十倍

### 6.1 breakpoint()：零配置的调试器

在想暂停的地方写一行 `breakpoint()`，运行到那里程序会停下，进入交互模式：

```python
def calc_total(items):
    breakpoint()          # ← 程序在这暂停
    return sum(item["price"] for item in items)
```

停下后你可以直接输入变量名查看值，常用命令：

| 命令 | 作用 |
|---|---|
| `p items` | 打印变量（print） |
| `n` | 执行下一行（next） |
| `s` | 进入函数内部（step in） |
| `c` | 继续运行到下一个断点（continue） |
| `l` | 显示当前位置的代码（list） |
| `q` | 退出调试（quit） |

### 6.2 VSCode 图形化调试（推荐日常使用）

1. 在行号左侧**点一下**打红点（断点）
2. 左侧栏「运行和调试」→ **Run and Debug** → 选 `Python File`
   （调试 FastAPI 时选 `Python Debugger: FastAPI`，VSCode 会自动生成配置）
3. 程序停在断点处后：
   - 左侧面板直接看到**所有变量的当前值**
   - 顶部按钮：继续（F5）/ 单步跳过（F10）/ 单步进入（F11）
   - 底部「调试控制台」可以执行任意表达式，如 `len(items)`

> **要点**：print 调试一次只能看一个值、改一次跑一次；
> 断点调试暂停在现场，**所有变量随便看、随便算**。花 30 分钟学会它，之后每天都省时间。

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 日志一条都不输出 | 级别设太高 / logger 没 handler | 检查 `basicConfig` 的 `level`；确认入口执行过配置 |
| `logger.debug` 不显示 | 默认级别是 WARNING | `basicConfig(level=logging.DEBUG)` |
| 日志重复输出两遍 | `basicConfig` 被调用多次 / handler 加了两次 | 只在程序入口配置一次 |
| 日志文件乱码 | 没指定编码 | handler 加 `encoding="utf-8"` |
| `breakpoint()` 忘了删，程序卡住 | —— | 提交前全局搜索 `breakpoint`（可加进 flake8 检查） |
| 中文日志在某些终端乱码 | 终端编码问题 | 用 VSCode 内置终端；文件输出指定 utf-8 |

---

## 小练习

1. 写一个脚本：配置 logging 同时输出到屏幕和 `app.log`（1MB 轮转，保留 2 份），
   依次打出五个级别的日志，观察 `level=INFO` 时哪些出现了。
2. 故意制造一个 `KeyError`，分别用 `logger.error(f"{e}")` 和 `logger.exception(...)` 记录，
   对比日志文件里的差异。
3. 写一个含 bug 的函数（比如处理一个缺键的字典列表），先只靠**读 traceback** 定位，
   再用 `breakpoint()` 验证你的判断。
4. 在 VSCode 里给第 3 题打断点，观察变量面板，练习 F10 / F11 单步。

> 下一章：[04 · FastAPI 入门](04-fastapi-basics.md) —— 带着日志和调试能力，正式开始写 API！
