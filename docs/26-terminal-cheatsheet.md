# 26 · 终端命令速查与实战

> 全书用过的终端命令都散在各章。本章把它们**收拢 + 补全**：从基础操作到数据库交互的组合拳，
> 按"你想干什么"组织，方便随时回来查。
> 定位是**附录**——不需要从头读到尾，先通读一遍第 1、9 节（认知和安全），其余当字典用。

---

## 学习目标

1. 建立终端的基本心智模型（路径、补全、中断）
2. 熟练文件/目录操作与文本查看（尤其**看日志**）
3. 会排查"端口被占用"、会管理进程——本书最高频的实战场景
4. 掌握 `sqlite3` 命令行的进阶用法：格式化输出、备份、导出 CSV
5. 会用管道 `|` 把命令组合成"一句话工具"
6. 背下危险命令清单，养成安全习惯

---

## 1. 基础认知：让终端不再陌生

```bash
# 你看到的 "xxx@MacBook ~ %" 叫提示符（prompt），% 或 $ 后面才是你输入的命令
# 命令的通用结构：
命令 -选项 参数
ls   -la  /Users        # ls 是命令，-la 是选项（可合写），/Users 是参数
```

**四个改变人生的按键**（比背任何命令都重要）：

| 按键 | 作用 |
|---|---|
| `Tab` | **自动补全**文件名/命令——路径永远别手打全，打头几个字母按 Tab |
| `↑` / `↓` | 翻历史命令——重复执行昨天的命令不用重敲 |
| `Ctrl + C` | **中断**当前程序（停掉 uvicorn / 卡住的命令）|
| `Ctrl + A` / `Ctrl + E` | 光标跳行首 / 行尾（改长命令时救命）|

**路径心智模型**（每个命令都在"某个位置"执行）：

```bash
pwd            # 我现在在哪（print working directory）
~              # 你的家目录 /Users/你的用户名
.              # 当前目录          ..    # 上一级目录
cd demo        # 进入（相对路径）   cd ..  # 回上级
cd ~/dev       # 绝对路径（从家出发）
cd -           # 回到上一个待过的目录（来回切换神器）
```

---

## 2. 文件与目录操作

```bash
ls             # 列出当前目录
ls -la         # 含隐藏文件（.env / .git 都是隐藏的！）+ 详细信息
ls demo/       # 看别的目录，不用 cd 过去

mkdir docs                 # 建目录
mkdir -p app/db/models     # -p：一路建到底，父目录不存在也不报错

touch main.py              # 建空文件（或更新时间戳）

cp a.py b.py               # 复制文件
cp -r demo demo_backup     # 复制目录必须 -r（recursive）

mv a.py app/               # 移动
mv old.py new.py           # 重命名（移动和重命名是同一个命令）

rm a.py                    # 删文件 ⚠️ 不进废纸篓，直接消失
rm -r build/               # 删目录 ⚠️ 见第 9 节危险清单

open .                     # macOS：在访达中打开当前目录
open index.html            # 用默认程序打开文件（浏览器/编辑器）
```

---

## 3. 查看与搜索文本（后端排障的主战场）

```bash
cat app.log                # 整个文件打到屏幕（小文件用）
head -20 app.log           # 只看前 20 行
tail -50 app.log           # 只看最后 50 行（日志通常看尾部！）
tail -f app.log            # ★ 实时跟踪：新日志一来就滚动显示——排障必备
less app.log               # 分页阅读大文件（空格翻页 / 输入 /关键词 搜索 / q 退出）

grep "ERROR" app.log            # 在文件里找包含 ERROR 的行
grep -n "ERROR" app.log         # -n 顺带显示行号
grep -i "error" app.log         # -i 忽略大小写
grep -r "get_db" app/           # -r 在整个目录里递归搜（找代码在哪定义的）
grep -rn "TODO" . --include="*.py"   # 只搜 .py 文件

find . -name "*.db"             # 按文件名找文件（"我的数据库文件建到哪去了？"）
find . -name "__pycache__" -type d   # 找目录

wc -l app.log                   # 数行数（日志今天涨了多少）
```

---

## 4. 进程与端口（本书最高频的实战）

"端口被占用"、"服务关不掉"——全在这一节：

```bash
lsof -i :8000              # ★ 谁占着 8000 端口？（显示进程名和 PID）
kill 12345                 # 按 PID 温柔地终止进程
kill -9 12345              # 强制终止（温柔的没反应时才用）
pkill -f "uvicorn"         # 按命令名模糊匹配并终止（本书用过多次）

ps aux | grep python       # 列出所有 python 相关进程
ps aux | grep -v grep | grep uvicorn   # 排除 grep 自己那行（经典组合）

command &                  # 结尾加 & = 后台运行（终端还能继续用）
jobs                       # 看当前终端的后台任务
fg                         # 把后台任务调回前台（然后可 Ctrl+C）
```

**排障剧本**（Address already in use 时照做）：

```bash
lsof -i :8000        # ① 找到占用者的 PID
kill <PID>           # ② 终止它
lsof -i :8000        # ③ 确认端口已空
```

---

## 5. 网络与环境

```bash
curl -s "http://127.0.0.1:8000/todos" | python3 -m json.tool
                           # 请求 API 并格式化 JSON（10 章的老朋友，组合拳见第 7 节）
ping baidu.com             # 网络通不通（Ctrl+C 停止）
which python3              # 这个命令的可执行文件在哪（排查"用的到底是哪个 python"）
which uvicorn              # 验证虚拟环境是否激活的妙招：路径应含 .venv
ipconfig getifaddr en0     # macOS 查本机局域网 IP（11 章手机联调用过）

echo $PATH                 # 查看环境变量
export API_KEY="xxx"       # 设置环境变量（当前终端有效，08 章讲过持久化方案）
env | grep ANTHROPIC       # 列出匹配的环境变量
```

**本书项目命令全家福**（都学过，集中列在一处）：

```bash
python3 -m venv .venv && source .venv/bin/activate    # 01 章
pip install -r requirements.txt                       # 01 章
uvicorn main:app --reload                             # 04 章
uvicorn app.main:app --reload                         # 20 章（包结构）
python3 -m http.server 3000                           # 18/21 章（前端服务器）
pytest -v                                             # 10 章
git status / add / commit / push                      # 02 章
docker build -t name . && docker run -p 8000:8000 name   # 11 章
```

---

## 6. sqlite3 命令行：与数据库交互的完整功夫

05 章只用了 `.tables` 和 SELECT，这里是完整版。先进入交互模式：

```bash
sqlite3 todos.db           # 打开数据库（进入 sqlite> 提示符，.quit 退出）
```

### 6.1 让查询结果变得能看

默认输出是竖线分隔的裸文本，先调格式：

```sql
.headers on        -- 显示列名
.mode box          -- 表格化输出（漂亮的框线；老版本可用 .mode column）
SELECT * FROM todos LIMIT 5;

-- ┌────┬───────────────┬──────┐
-- │ id │     title     │ done │      ← 从"没法看"变成"一目了然"
-- ├────┼───────────────┼──────┤
```

### 6.2 探查结构

```sql
.tables                    -- 有哪些表
.schema todos              -- 这张表的建表语句
.schema                    -- 所有表的建表语句
PRAGMA table_info(todos);  -- 表结构的表格视图（列名/类型/非空/默认值）
```

### 6.3 一句话模式：不进交互界面直接执行

把 SQL 作为参数传入——**可以写进脚本、可以接管道**，这是它比交互模式强大的地方：

```bash
sqlite3 todos.db "SELECT COUNT(*) FROM todos;"
sqlite3 -box -header todos.db "SELECT * FROM todos WHERE done = 0;"
sqlite3 todos.db "DELETE FROM todos WHERE done = 1;"      # ⚠️ 改数据也可以，小心

# 组合拳：每天数一下数据量并追加到记录文件
echo "$(date +%F): $(sqlite3 todos.db 'SELECT COUNT(*) FROM todos;')" >> stats.log
```

### 6.4 备份与恢复（上线前检查清单里的"备份策略"落地）

```bash
# 方式一：在线备份命令（推荐——服务运行中也安全）
sqlite3 todos.db ".backup backup_$(date +%F).db"

# 方式二：导出为 SQL 文本（可读、可进 Git 做样本数据）
sqlite3 todos.db .dump > backup.sql
sqlite3 new.db < backup.sql        # 从 SQL 文本恢复出一个新库

# 直接 cp 也行，但必须先停服务（写入中复制可能损坏）
```

### 6.5 导出 CSV（给 Excel / 给同事）

```bash
sqlite3 -csv -header todos.db "SELECT * FROM todos;" > todos.csv
```

---

## 7. 管道与重定向：把命令拼成工具

**心智模型**：`|` 把左边命令的输出，喂给右边命令当输入——像乐高一样拼接：

```bash
命令A | 命令B | 命令C      # A 的结果给 B 加工，B 的结果给 C 加工

# 重定向：输出去文件而不是屏幕
命令 > 文件      # 覆盖写入 ⚠️ 原内容清空
命令 >> 文件     # 追加写入
命令 2>&1        # 把错误输出也一起收进来（uvicorn 日志重定向常用）
```

**本书场景的实用组合拳**：

```bash
# API 返回的 JSON 格式化着看
curl -s http://127.0.0.1:8000/todos | python3 -m json.tool

# 日志里今天有多少个 ERROR
grep "ERROR" app.log | wc -l

# 实时只看含 WARNING 以上的日志
tail -f app.log | grep -E "WARNING|ERROR"

# 找出上传目录里最大的 5 个音频文件（音频项目实用）
ls -lhS uploads/ | head -6

# 整个项目多大（排除虚拟环境）
du -sh . --exclude=.venv 2>/dev/null || du -sh .

# 历史命令里找"我上次那条 docker 命令怎么写的"
history | grep docker

# 后台跑服务并把日志收进文件
uvicorn main:app > server.log 2>&1 &
tail -f server.log
```

---

## 8. 让日常更顺手（可选进阶）

```bash
# 别名：把长命令绑成短名字（写进 ~/.zshrc 永久生效）
alias va="source .venv/bin/activate"
alias gs="git status"
alias serve="python3 -m http.server 3000"

# && 与 ;：串联多条命令
cd demo && source .venv/bin/activate    # && = 前一条成功才执行后一条
mkdir tmp; cd tmp                       # ;  = 不管成败都继续

# !! ：上一条命令原样重放（配 sudo 特别顺手：sudo !!）
```

改完 `~/.zshrc` 后执行 `source ~/.zshrc` 生效。

---

## 9. 危险命令清单（背下来）

| 命令 | 危险在哪 | 安全习惯 |
|---|---|---|
| `rm -rf 路径` | 递归强制删除，**无废纸篓、无确认、无后悔药**；路径手滑多个空格可能删掉不相干目录 | 删除前先 `ls 同样的路径` 看一眼要删的是什么；永远不要执行别人给的 `rm -rf /` 类命令 |
| `>` 重定向 | 目标文件**原内容瞬间清空**——手滑把 `>>` 打成 `>`，日志就没了 | 追加一律用 `>>`；重要文件先备份 |
| `sudo 任意命令` | 以管理员身份执行，错误被放大 | 本书全程**不需要** sudo；网上教程叫你 sudo pip install 的都别照做（污染系统 Python）|
| `kill -9` | 强杀不给程序清理机会（数据库写一半可能损坏）| 先普通 `kill`，无效再 -9 |
| `mv a b` | b 已存在时**直接覆盖不提示** | 移动前 `ls` 确认目标 |
| 粘贴来路不明的命令 | 你看不懂的命令可能干任何事 | 不懂的命令先问 AI"这条命令做什么"，看懂再执行 |

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `command not found` | 命令没安装 / venv 没激活 / PATH 问题 | `which 命令名` 排查；先激活虚拟环境 |
| `No such file or directory` | 当前位置不对 / 路径拼错 | `pwd` 看在哪，`ls` 看有什么，Tab 补全代替手打 |
| `Permission denied` | 没有执行/写入权限 | 确认操作的是自己的文件；脚本需 `chmod +x` |
| `Address already in use` | 端口被占 | 第 4 节的三步剧本 |
| 终端卡住不动 | 程序在前台运行 / less 等待输入 | `Ctrl+C` 中断；less/git log 按 `q` 退出 |
| sqlite3 里命令没反应 | SQL 忘了分号 / 点命令带了分号 | SQL 以 `;` 结尾；`.tables` 这类点命令**不加**分号 |
| 改了 .zshrc 没生效 | 没重新加载 | `source ~/.zshrc` 或开新终端 |

---

## 小练习

1. 用 `tail -f` 跟踪 demo 的日志，另开终端 curl 几个接口，观察日志实时滚动。
2. 故意再启动一个 uvicorn 制造端口冲突，用第 4 节的三步剧本解决它。
3. 给 demo 的 todos.db：调好 `.mode box`，跑一条 JOIN 查询（21 章学的），
   然后 `.backup` 一份、再导一份 CSV 用表格软件打开。
4. 写一条你自己的组合拳：统计 demo 的 `app/` 目录下所有 .py 文件的总行数
   （提示：`find` + `cat` 或 `wc`，答案不唯一）。
5. 把你最常敲的三条长命令做成 alias，用一周。

> 📌 本章是附录，会随全书持续补充。遇到"这条命令是什么意思"时，先回来查这里，再问搜索引擎/AI。
