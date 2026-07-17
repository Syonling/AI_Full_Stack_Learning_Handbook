# 05 · SQLite 基础

> 本章目标：学会用 SQL 语句和 Python 的 `sqlite3` 标准库对数据库做增删改查。
> 预计学习时间：3~4 小时。本章代码不需要 FastAPI，可以在任何 .py 文件里直接练。
::: details 关联教程
[零基础入门学习「SQLite」](https://www.bilibili.com/video/BV1zy411i7UV)
:::

---

## 学习目标

1. 理解数据库、表、行、列的概念
2. 会写四大类 SQL：`SELECT` / `INSERT` / `UPDATE` / `DELETE`
3. 用 Python `sqlite3` 模块连接数据库并执行 SQL
4. 掌握**参数化查询**（防 SQL 注入，必须养成的习惯）
5. 理解事务和 `commit`

---

## 1. 什么是 SQLite？

- **数据库（database）**：长期保存数据的地方。程序重启后内存里的变量都会消失，数据库里的数据不会。
- **SQLite**：最轻量的关系型数据库——整个数据库就是**一个文件**（如 `app.db`），
  不需要安装任何服务器软件，Python 标准库自带驱动（`import sqlite3` 即可用）。

数据的组织方式（关系型数据库都一样）：

```
数据库 app.db
└── 表 todos（像一张 Excel 表格）
      ┌────┬───────────────┬──────┐
      │ id │ title         │ done │   ← 列（column）：字段
      ├────┼───────────────┼──────┤
      │ 1  │ learn python  │ 1    │   ← 行（row）：一条记录
      │ 2  │ learn fastapi │ 0    │
      └────┴───────────────┴──────┘
```

SQLite 常用数据类型：

| 类型 | 说明 | 对应 Python |
|---|---|---|
| INTEGER | 整数 | int |
| REAL | 小数 | float |
| TEXT | 文本 | str |
| BLOB | 二进制 | bytes |
| —— | SQLite 没有布尔类型，用 0/1 代替 | bool → 0/1 |

---

## 2. 连接数据库与建表

```python
import sqlite3

# 连接数据库文件（不存在会自动创建）
conn = sqlite3.connect("app.db")

# 游标（cursor）：执行 SQL 的工具
cursor = conn.cursor()

# 建表（IF NOT EXISTS：表已存在就跳过，可以安全地重复执行）
cursor.execute("""
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        done INTEGER DEFAULT 0
    )
""")

conn.commit()      # 提交：让修改真正生效
conn.close()       # 用完关闭连接
```

建表语句逐行解读：

- `id INTEGER PRIMARY KEY AUTOINCREMENT` —— 主键，每条记录的唯一编号，插入时自动 +1，不用手动指定
- `title TEXT NOT NULL` —— 文本字段，不允许为空
- `description TEXT DEFAULT ''` —— 有默认值的可选字段
- `done INTEGER DEFAULT 0` —— 用 0/1 表示 False/True

---

## 3. 增：INSERT

```python
import sqlite3

conn = sqlite3.connect("app.db")
cursor = conn.cursor()

# ？是占位符，实际值通过第二个参数（元组）传入 —— 这叫"参数化查询"
cursor.execute(
    "INSERT INTO todos (title, description) VALUES (?, ?)",
    ("learn sqlite", "chapter 04"),
)

# 拿到刚插入记录的自增 id（很常用！）
new_id = cursor.lastrowid
print(f"inserted id = {new_id}")

conn.commit()      # INSERT/UPDATE/DELETE 之后必须 commit，否则数据不会保存！
conn.close()
```

> **⚠️ 必须用参数化查询，禁止用 f-string 拼 SQL：**
>
> ```python
> # ❌ 危险！如果 title 来自用户输入，恶意输入可以篡改 SQL（SQL 注入攻击）
> cursor.execute(f"INSERT INTO todos (title) VALUES ('{title}')")
>
> # ✅ 正确：用 ? 占位，sqlite3 会安全地处理值
> cursor.execute("INSERT INTO todos (title) VALUES (?)", (title,))
> ```
>
> 注意 `(title,)` 结尾的逗号——只有一个值时也必须是元组。

---

## 4. 查：SELECT

```python
import sqlite3

conn = sqlite3.connect("app.db")
# Row 工厂：让查询结果可以用列名访问（强烈推荐，默认只能用序号）
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# ── 查所有行 ──
cursor.execute("SELECT * FROM todos")
rows = cursor.fetchall()              # 拿到所有结果（列表）
for row in rows:
    print(row["id"], row["title"], row["done"])

# ── 查单行 ──
cursor.execute("SELECT * FROM todos WHERE id = ?", (1,))
row = cursor.fetchone()               # 拿一行；没有结果时返回 None
if row is None:
    print("not found")
else:
    print(dict(row))                  # Row 可以直接转 dict → 方便返回 JSON

conn.close()
```

### SELECT 的常用变化

```sql
-- 只取部分列
SELECT id, title FROM todos;

-- WHERE 条件过滤
SELECT * FROM todos WHERE done = 0;
SELECT * FROM todos WHERE id = 3;
SELECT * FROM todos WHERE title LIKE '%fastapi%';    -- 模糊匹配（包含 fastapi）
SELECT * FROM todos WHERE done = 0 AND id > 5;       -- 多条件 AND / OR

-- 排序：ORDER BY ... ASC 升序（默认）/ DESC 降序
SELECT * FROM todos ORDER BY id DESC;

-- 限制条数 + 跳过（分页的基础）
SELECT * FROM todos LIMIT 10;                  -- 只要 10 条
SELECT * FROM todos LIMIT 10 OFFSET 20;        -- 跳过前 20 条，取 10 条（第 3 页）

-- 统计数量
SELECT COUNT(*) FROM todos WHERE done = 1;
```

> **要点**：`fetchone()` 返回一行或 `None`；`fetchall()` 返回列表（可能为空 `[]`）。
> 查询（SELECT）不需要 commit，只有修改数据才需要。

---

## 5. 改：UPDATE

```python
cursor.execute(
    "UPDATE todos SET title = ?, done = ? WHERE id = ?",
    ("learn sqlite well", 1, 1),
)
print(f"updated rows: {cursor.rowcount}")   # 受影响的行数；0 说明 id 不存在
conn.commit()
```

> **⚠️ 最危险的错误：忘写 WHERE。**
> `UPDATE todos SET done = 1` （没有 WHERE）会把**整张表所有行**都改掉！
> UPDATE 和 DELETE 语句写完先检查一遍有没有 WHERE。

---

## 6. 删：DELETE

```python
cursor.execute("DELETE FROM todos WHERE id = ?", (2,))
print(f"deleted rows: {cursor.rowcount}")   # 0 说明这个 id 本来就不存在
conn.commit()
```

`cursor.rowcount` 是判断"删除/更新的目标是否存在"的标准方式——
在 API 里可以据此决定返回 200 还是 404。

---

## 7. 事务与 commit

SQLite 默认工作在"事务"模式：**你执行的修改先记在"草稿"里，`commit()` 才真正写入文件。**

```python
conn = sqlite3.connect("app.db")
cursor = conn.cursor()

try:
    # 一组必须"同生共死"的操作（比如转账：扣钱和加钱必须同时成功）
    cursor.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
    cursor.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
    conn.commit()               # 两步都成功 → 一起生效
except Exception:
    conn.rollback()             # 任何一步出错 → 全部撤销，回到修改前
    raise                       # 不带参数 = 把异常原样再抛出（01 章第 5 节讲过）
finally:
    conn.close()
```

> **要点**：初学阶段记住两条就够——
> ① 增删改之后要 `commit()`；② 出错时 `rollback()` 可以撤销未提交的修改。

---

## 8. 实用技巧

### 8.1 用 with 自动管理连接

```python
# with 块结束时自动 commit（出异常则自动 rollback）。注意：不会自动 close
with sqlite3.connect("app.db") as conn:
    conn.execute("INSERT INTO todos (title) VALUES (?)", ("auto commit",))
conn.close()
```

### 8.2 一次插入多条 executemany

```python
items = [("task a",), ("task b",), ("task c",)]
cursor.executemany("INSERT INTO todos (title) VALUES (?)", items)
conn.commit()
```

### 8.3 查看数据库里有什么（调试用）

```python
# 列出所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cursor.fetchall())

# 查看表结构
cursor.execute("PRAGMA table_info(todos)")
for col in cursor.fetchall():
    print(col)
```

也可以在终端里用 sqlite3 命令行工具直接查看（macOS 自带）：

```bash
sqlite3 app.db
# 进入交互模式后：
# .tables          列出所有表
# .schema todos    查看建表语句
# SELECT * FROM todos;
# .quit            退出
```

### 8.4 conn.execute()：跳过 cursor 的快捷方式（07 章起会大量使用）

到目前为止我们都是标准三步：`connect → cursor() → execute`。
其实 **Connection 对象自带 execute 快捷方式**——内部自动新建一个 cursor、执行 SQL、
再把这个 cursor **返回给你**：

```python
# 标准三步（本章之前的写法）
cursor = conn.cursor()
cursor.execute("SELECT * FROM todos WHERE done = ?", (0,))
rows = cursor.fetchall()

# 快捷方式：三行并一行 —— execute 返回的就是 cursor，所以能直接链式调用
rows = conn.execute("SELECT * FROM todos WHERE done = ?", (0,)).fetchall()
new_id = conn.execute("INSERT INTO todos (title) VALUES (?)", ("x",)).lastrowid
```

两种写法**完全等价**。单条语句用快捷方式更省行——**从 07 章起，教程代码统一用这种写法**，
在那里见到 `db.execute(...).fetchone()` 不要慌，它就是"自动帮你建了 cursor"。

---

## 常见错误与排查

| 错误 | 原因 | 解决 |
|---|---|---|
| 数据"没保存"，重启后消失 | 忘了 `conn.commit()` | 增删改后必须 commit |
| `sqlite3.OperationalError: no such table: todos` | 表没建 / 连到了另一个 db 文件 | 先执行建表语句；检查文件路径（相对路径取决于运行目录！） |
| `sqlite3.IntegrityError: NOT NULL constraint failed` | 必填字段没给值 | 检查 INSERT 是否包含所有 NOT NULL 字段 |
| `sqlite3.ProgrammingError: Incorrect number of bindings` | ? 的个数和参数元组长度不一致 | 单个参数记得写成 `(x,)` |
| 整张表被改光了 | UPDATE/DELETE 没写 WHERE | 没有后悔药……写 SQL 先写 WHERE 的习惯 |
| 查询结果只能用 `row[0]` 访问 | 没设置 row_factory | `conn.row_factory = sqlite3.Row` |

---

## 小练习

新建一个 `practice_db.py`，依次完成：

1. 创建 `books` 表：`id`（主键自增）、`title`（TEXT 非空）、`author`（TEXT）、`price`（REAL 默认 0）。
2. 用 `executemany` 一次插入 3 本书。
3. 查询所有 price > 50 的书，按价格降序排列，用 `dict(row)` 打印每一行。
4. 把某本书的价格改成 99.9，打印 `rowcount` 确认成功。
5. 删除一本书，再查一次确认删掉了。
6. 用终端 `sqlite3` 命令行打开数据库文件，`.tables` 和 `SELECT` 验证。

> 下一章：[07 · FastAPI + SQLite 整合](07-fastapi-sqlite-crud.md) —— 把这两章的知识拼成完整后端！
