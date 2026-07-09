# 20 · 后端代码组织：FastAPI 项目的分层与拆分

> 18 章讲了前端的工程优雅，这章是 Python 版：目录怎么分层、模块怎么拆、
> 循环导入怎么破。10 章的"项目结构演进"是预告片，本章是正片。
> 预计学习时间：3~4 小时。需要 07（整合实战）、09（工程化）、10（测试与结构）。
> 建议学完 10 章后即可阅读本章，不必等 11 章。

---

## 学习目标

1. 理解**分层思想**：路由层 / 业务层 / 数据层 / 模型层各管什么
2. 掌握中型 FastAPI 项目的标准目录结构（可直接套用）
3. 理解 Python 包（package）与 `__init__.py`
4. 会诊断和解除**循环导入**——多文件项目的头号拦路虎
5. 知道什么时候该拆、什么时候不该拆（不过度设计）

---

## 1. 分层思想：每层只回答一个问题

demo 的三文件结构（main / database / schemas）其实已经是分层的雏形。把它说透：

| 层 | 回答的问题 | demo 里的对应 | 演进后 |
|---|---|---|---|
| **路由层** | "HTTP 请求怎么进出？"（路径、参数、状态码）| main.py 的路由函数 | `routers/` |
| **业务层** | "规则是什么？"（能不能删、怎么算、先后顺序）| 混在路由函数里 | `services/` |
| **数据层** | "数据怎么存取？"（SQL、连接管理）| database.py | `db/` 或保持 database.py |
| **模型层** | "数据长什么样？"（字段、校验）| schemas.py | `schemas/` |

**判断代码该放哪一层的速查法**：这段代码提到了 `request`/状态码吗 → 路由层；
提到了 SQL 吗 → 数据层；都没提、纯粹是"规矩" → 业务层。

分层的核心收益是**依赖方向单一**：

```
routers  ──▶  services  ──▶  db
   │             │            
   └──────┬──────┘            
          ▼                   
       schemas（模型层被上面各层引用，自己不引用任何人）
       core（config/日志同理：只被引用，不引用业务）
```

**箭头永远向下、永远单向**——记住这张图，第 4 节的循环导入问题就有了答案。

---

## 2. 标准目录结构（模板，直接套用）

```
my_project/
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py           # 声明 app 是一个"包"（见第 3 节）
│   ├── main.py               # 只做组装：创建 app、挂中间件、include 路由
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py         # 08 章的 Settings
│   │   └── logging.py        # 03 章的日志配置，抽成函数 setup_logging()
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py       # 连接、init_db、get_db
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── todo.py           # TodoCreate / TodoUpdate / TodoOut
│   │   └── user.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── todo_service.py   # 业务逻辑（什么时候需要它见第 5 节）
│   └── routers/
│       ├── __init__.py
│       ├── todos.py          # APIRouter（06 章学过）
│       └── users.py
└── tests/
    ├── __init__.py
    └── test_todos.py
```

组装后的 main.py 瘦成这样（**入口文件越瘦，项目越健康**）：

```python
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.database import lifespan          # init_db 挪进 lifespan
from app.routers import todos, users

setup_logging(settings.log_level)

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(todos.router)
app.include_router(users.router)
```

> **要点**：文件按"资源"切，不按"动词"切——`routers/todos.py` 装下 todos 的全部五个接口，
> 而不是 `create.py / delete.py` 各放一个函数。和 18 章"相关的放一起"同理。

---

## 3. Python 包与 `__init__.py`

**包（package）= 带 `__init__.py` 的文件夹**。这个空文件是给 Python 看的标记：
"这个文件夹是代码的一部分，可以用点号导入"：

```python
from app.routers.todos import router      # app/routers/todos.py
from app.core.config import settings      # app/core/config.py
```

两个新手必踩的坑：

1. **`__init__.py` 通常留空即可**——它可以写代码（比如在里面做汇总导出），但初学阶段空文件最safe
2. **启动位置变了**：包结构下 uvicorn 要在**项目根目录**（app 的上一级）启动，模块路径带包名：

   ```bash
   # 在 my_project/ 目录下（不是 app/ 里！）
   uvicorn app.main:app --reload
   ```

   demo 之所以在 app/ 里启动 `uvicorn main:app`，是因为它还没用包结构——两种都对，取决于结构。

---

## 4. 循环导入：多文件项目的头号拦路虎

### 症状

```
ImportError: cannot import name 'get_db' from partially initialized module
'app.db.database' (most likely due to a circular import)
```

### 成因

A 导入 B，B 又导入 A——Python 加载到一半发现绕回来了：

```python
# ── routers/todos.py ──
from app.services.todo_service import create_todo     # routers → services

# ── services/todo_service.py ──
from app.routers.todos import some_helper             # services → routers ❌ 回头了！
```

### 解法（按优先级）

1. **首选：检查依赖方向**。回看第 1 节的箭头图——`services` 反过来依赖 `routers`
   本身就是设计错了。低层永远不该 import 高层。
2. **公共的下沉**：A 和 B 都需要的东西（工具函数、常量、模型），说明它不属于任何一方——
   下沉到更低层（schemas / core / utils），双方都从下面拿。
3. **最后手段：局部导入**（把 import 挪进函数体内，用时才加载）——能解燃眉之急，
   但它是在掩盖设计问题，用了要留注释说明。

> **要点**：循环导入报错不是"Python 的坑"，是**架构在报警**——两个模块粘得太紧了。
> 90% 的场景用"公共的下沉"就能优雅解决。

---

## 5. 什么时候拆 service 层？（防过度设计）

**不是所有项目都需要 services/**。demo 的路由函数直接写 SQL 完全正确——因为逻辑就三行。拆分信号：

| 信号 | 例子 |
|---|---|
| 路由函数超过 ~30 行 | 参数处理 + 三次查询 + 计算 + 组装响应挤在一起 |
| 同一段业务逻辑被两个接口复用 | "计算订单总价"被下单和预览两个接口调用 |
| 想单独测试业务规则 | 不想每个测试都走一遍 HTTP |

拆分后的样子：

```python
# ── services/todo_service.py：纯业务，不认识 HTTP ──
def complete_todo(db, todo_id: int) -> dict | None:
    """标记完成。返回更新后的记录，不存在返回 None。"""
    row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        return None                      # ← 不抛 HTTPException！那是路由层的词汇
    db.execute("UPDATE todos SET done = 1 WHERE id = ?", (todo_id,))
    db.commit()
    return dict(db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone())

# ── routers/todos.py：只做 HTTP 翻译 ──
@router.put("/{todo_id}/complete", response_model=TodoOut)
def complete(todo_id: int, db=Depends(get_db)):
    result = todo_service.complete_todo(db, todo_id)
    if result is None:
        raise HTTPException(404, f"todo {todo_id} not found")   # HTTP 词汇留在这
    return result
```

注意分界线：**service 返回 None，router 把它翻译成 404**——业务层不认识 HTTP，
这样同一个 service 将来给定时任务、CLI 脚本、Agent 工具（12 章）复用时都不用改。

### 演进路线图（对照 10 章）

```
阶段一 单文件            → 学习/原型（04 章的起点）
阶段二 三文件            → demo 现状，< 10 个接口完全够用
阶段三 routers/schemas 拆包 → 接口变多（10 章讲过）
阶段四 + services/core     → 业务逻辑变厚（本章）
```

**规则不变：结构跟着复杂度走，晚拆好过早拆。**

---

## 6. 命名规范：PEP 8 速查

Python 官方风格指南 PEP 8 中最常用的部分：

| 对象 | 规范 | 例子 |
|---|---|---|
| 变量 / 函数 | snake_case（小写下划线）| `todo_list`、`get_db` |
| 类 / Pydantic 模型 | PascalCase（大驼峰）| `TodoCreate`、`Settings` |
| 常量 | 全大写下划线 | `DB_PATH`、`MAX_RETRIES` |
| 模块 / 包（文件夹）| 全小写，短 | `database.py`、`routers/` |
| "私有"约定 | 单下划线开头 | `_build_query`（提示：外部别用）|

配套工具（对应 18 章的 Prettier）：**Ruff**——Python 界的格式化+检查二合一，
`pip install ruff` 后 `ruff format .` 一键统一全项目风格，VSCode 也有同名插件可开保存即格式化。

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `ModuleNotFoundError: No module named 'app'` | 启动位置不对 | 到项目根目录（app 的上一级）运行 `uvicorn app.main:app` |
| `attempted relative import with no known parent package` | 缺 `__init__.py` / 直接 python 运行了包内文件 | 补 `__init__.py`；用 uvicorn/`python -m` 方式启动 |
| circular import 报错 | 依赖方向绕环 | 第 4 节三步：查方向 → 公共下沉 → 局部导入 |
| 拆完文件后 import 满天飞很乱 | 按动词拆而不是按资源拆 | 一个资源一个文件（todos 的所有接口在一起）|
| service 里出现 HTTPException | 层的词汇越界 | service 返回 None/抛业务异常，router 负责翻译成 HTTP |
| 到处 `from app.core.config import settings` 感觉重复 | —— | 这是正常且正确的——显式导入优于全局魔法 |

---

## 小练习

1. （纸上练习）给 demo 的五个路由函数逐一判断：如果按第 2 节结构拆分，
   每个函数的每一行分别属于哪一层？
2. 动手把 demo 复制一份，改造成第 2 节的包结构（routers/schemas/core/db 四个包），
   在根目录用 `uvicorn app.main:app --reload` 跑通，/docs 里五个接口不变。
3. 故意制造一次循环导入（routers 和 services 互相 import），看清报错长相，
   再用"公共下沉"解掉它。
4. `pip install ruff`，对你的练习项目跑 `ruff format .` 和 `ruff check .`，修掉所有警告。

> 配合阅读：[10 · 测试与项目结构](10-testing-and-structure.md)（结构演进的全景）、
> [18 · 前端工程组织](18-frontend-engineering.md)（同一套思想的前端版）。
