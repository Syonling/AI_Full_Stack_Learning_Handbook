# 27 · 用户登录与身份认证

> 本章目标：给 API 加上账号系统——密码安全存储、注册/登录接口、JWT 令牌、保护路由、前端配合。
> 预计学习时间：4~5 小时。前置：06（Pydantic/Depends）、07（CRUD/异常处理）、08（密钥管理）、
> 09（错误处理套路）；20（分层思想）有助于理解代码该放哪。
> 本章为纯教学（不改动 demo），示例代码可直接加进你自己的项目。

---

## 学习目标

1. 分清**认证（Authentication）**和**授权（Authorization）**——一个问"你是谁"，一个问"你能干什么"
2. 理解为什么密码**永远不能明文存储**，会用哈希（hash）安全保存密码
3. 理解 **JWT** 是什么、为什么它天然契合本书一直在用的"无状态 API"架构
4. 实现注册、登录两个接口，以及一个"必须登录才能访问"的保护路由
5. 前端拿到令牌后怎么存、怎么在后续请求里带上
6. 一份上线前的安全检查清单

---

## 1. 概念地图：认证 vs 授权，Session vs Token

**认证**：你是谁——登录这一步，验证"这个密码对不对"。
**授权**：你能干什么——认证之后，判断"这个已登录用户能不能删这条记录"。
本章聚焦认证（登录），授权只在第 9 节点到为止（角色/权限体系是更大的话题）。

登录状态怎么维持？两条路线：

| 维度 | Session（服务端记状态）| Token / JWT（无状态）|
|---|---|---|
| 状态存在哪 | 服务器内存/Redis，靠 Cookie 里的 session id 关联 | 客户端自己存，服务端不存任何东西 |
| 多台服务器扩展 | 需要共享 session 存储，麻烦 | 天然无状态，加机器不用改架构 |
| 前后端分离场景 | 跨域 Cookie 处理繁琐 | 天然契合 `fetch` + `Authorization` 请求头 |
| 立即登出 | 服务端删记录，即时生效 | 需要额外机制（黑名单/短过期时间）|

> **要点**：HTTP 请求天生**互相独立**——服务器处理完这次请求就把它忘光，
> 下次请求过来必须**自带证明"我是谁"的完整信息**，服务器才知道你是谁。
> Token 正是这份"随身携带的证明"；这也是本章选择 JWT、而不是传统 session 的原因。

---

## 2. 密码安全：为什么不能明文存储

```
❌ users 表：username="alice", password="123456"
```

数据库一旦泄露（被拖库），所有用户的密码原样暴露——而大多数人到处用同一个密码，
后果远超出你这一个网站。正确做法：**只存密码的哈希值**，哈希是**单向**的（能算出结果，无法从结果反推原文）：

```python
# pip install "passlib[bcrypt]"
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

hashed = pwd_context.hash("my-password")
print(hashed)   # $2b$12$EixZaYVK1fsbw1ZfbX3OXe...（每次运行结果都不同！）

pwd_context.verify("my-password", hashed)      # True  —— 验证时重新哈希对比，不解密
pwd_context.verify("wrong-guess", hashed)      # False
```

> **要点**：`bcrypt` 每次哈希会自动加不同的**盐（salt）**，所以同一个密码两次哈希结果不同——
> 这是刻意设计，能防住"彩虹表"这类批量破解手段。你不需要自己管理盐，`passlib` 全自动处理。
> 千万别用 `md5`/`sha256` 直接哈希密码——那是给**文件**校验完整性用的，**不设计用来存密码**（太快，容易被暴力破解）。

---

## 3. 数据库设计：users 表

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,       -- ★ 新约束：这一列的值不允许重复
    password_hash TEXT NOT NULL,         -- 只存哈希，永不存明文
    created_at TEXT DEFAULT (datetime('now'))
);
```

`UNIQUE` 是本章第一次出现的新约束（05 章只教过 `NOT NULL` 和 `DEFAULT`）：
声明"这一列的值在整张表里不允许重复"，交给数据库自己把关——比在 Python 代码里
先 `SELECT` 查一遍"这个用户名是否已存在"再决定要不要插入更省心，也更安全
（两步之间可能有另一个请求插了同一个用户名进来，留下一个时间窗口的漏洞）。

插入重复用户名时，SQLite 会抛 `IntegrityError`——这正是 23 章处理
"素材被引用无法删除"时用过的同一个异常类型，这里复用来处理"用户名已占用"。

---

## 4. 注册接口

```python
# schemas/user.py
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)     # 前端也该校验，但后端这道不能省（13 章讲过的原则）

class UserOut(BaseModel):
    id: int
    username: str
```

```python
# routers/auth.py
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext

from app.db.database import get_db
from app.schemas.user import UserCreate, UserOut

router = APIRouter(tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    hashed = pwd_context.hash(user.password)
    try:
        cursor = db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (user.username, hashed),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名已被占用")
    row = db.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)     # UserOut 只声明了 id/username，password_hash 自动被过滤（06 章讲过）
```

> **要点**：`UserOut` 里没有 `password_hash` 字段——`response_model` 会自动把它从返回值里剔除，
> 这正是 06 章"response_model 过滤敏感字段"那节的真实应用场景，不是巧合。

---

## 5. JWT 是什么

**JWT（JSON Web Token）= 一段可以被任何人读、但不能被伪造的"签过名的通行证"**。长相是三段用 `.` 连接的字符串：

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhbGljZSIsImV4cCI6MTc4ODk5OTk5OX0.4f8a2b...
└────── header ──────┘└──────── payload ────────┘└── signature ──┘
   算法信息               谁、什么时候过期            服务端密钥签的名
```

- **header + payload 只是 Base64 编码，不是加密**——任何人复制粘贴到 [jwt.io](https://jwt.io) 都能看到里面写了什么
- **signature 才是安全核心**：服务端用只有自己知道的密钥（SECRET_KEY）对前两段签名。
  客户端如果篡改 payload（比如把用户名改成别人的），签名对不上，服务端立刻能识破

```python
# pip install "python-jose[cryptography]"
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "先别硬编码，第 6 节马上讲怎么正确管理"
ALGORITHM = "HS256"

token = jwt.encode(
    {"sub": "alice", "exp": datetime.utcnow() + timedelta(hours=2)},   # sub=谁, exp=何时过期
    SECRET_KEY, algorithm=ALGORITHM,
)
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])   # 密钥不对会抛 JWTError
```

> **要点**：`SECRET_KEY` 泄露 = 任何人都能伪造任意用户的令牌——它是全系统最高级别的秘密，
> **必须走 08 章的 `.env` 管理**，绝不写死在代码里、绝不进 Git。生成一个够随机的密钥：
>
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```
>
> 把结果存进 `.env` 的 `SECRET_KEY=`，`config.py` 的 `Settings` 里加一个**无默认值**的
> `secret_key: str`（08 章讲过：无默认值 = 忘配置直接启动报错，比运行到一半才炸更安全）。

---

## 6. 登录接口

```python
# routers/auth.py（续）
from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt

from app.core.config import settings   # settings.secret_key（第 5 节的密钥）

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT * FROM users WHERE username = ?", (form.username,)).fetchone()

    # 用户不存在 或 密码不对，返回同一句话——不要告诉攻击者"用户名对了，密码错了"
    if row is None or not pwd_context.verify(form.password, row["password_hash"]):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},   # 401 的标准约定头
        )

    token = jwt.encode(
        {"sub": row["username"], "exp": datetime.utcnow() + timedelta(hours=2)},
        settings.secret_key, algorithm="HS256",
    )
    return {"access_token": token, "token_type": "bearer"}
```

**`OAuth2PasswordRequestForm` 是一个坑点，务必注意**：它要求请求体是
`application/x-www-form-urlencoded`（表单格式），**不是 JSON**——这是 OAuth2 规范的约定写法。
需要 `pip install python-multipart`（23 章装过它，这里是第二个用武之地）。

> **要点**：`raise HTTPException(...)` 而不是 `return`，09 章讲过的规则在这里同样适用。
> "用户名或密码错误"这句**故意含糊**——分开报"用户名不存在" / "密码错误"会泄露"哪些用户名已注册"，
> 是一种叫**用户名枚举（enumeration）**的信息泄露，安全领域的标准忌讳。

---

## 7. 保护路由：只有登录用户能访问

```python
# core/security.py
import sqlite3

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.db.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")   # 告诉 /docs："去 /login 换令牌"

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "无法验证身份",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise unauthorized
    except JWTError:                      # 令牌过期/被篡改/格式不对，统一归为"无法验证"
        raise unauthorized

    row = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if row is None:
        raise unauthorized
    return dict(row)
```

用它保护任何路由——**只需在依赖里加一行**（06 章 Depends 的链式组合威力，此刻完全体现）：

```python
from app.core.security import get_current_user

@router.get("/todos")
def list_todos(
    current_user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    # 走到这一行，说明令牌已验证通过，current_user 就是当前登录的用户
    rows = db.execute("SELECT * FROM todos WHERE owner = ?", (current_user["username"],)).fetchall()
    return [dict(r) for r in rows]
```

`Depends(get_current_user)` 本身又依赖 `Depends(oauth2_scheme)`——**依赖可以一层套一层**，
FastAPI 会自动按顺序解析整条链。没带令牌或令牌无效，请求在进入 `list_todos` 函数体之前就被挡下，返回 401。

---

## 8. 前端整合：拿到令牌、之后怎么用

```javascript
// 登录：注意是表单编码，不是 JSON（对应第 6 节的坑点）
async function login(username, password) {
    const res = await fetch(`${API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username, password }),
    });
    if (!res.ok) throw new Error("登录失败");
    const { access_token } = await res.json();
    localStorage.setItem("token", access_token);   // 存起来，关掉浏览器还在
}

// 之后每个受保护请求，都带上 Authorization 头
async function getTodos() {
    const res = await fetch(`${API}/todos`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
    });
    if (res.status === 401) {
        localStorage.removeItem("token");
        // 引导用户重新登录
    }
    return res.json();
}
```

> **要点（安全权衡，了解即可）**：`localStorage` 简单好用，但能被同页面运行的任意 JS 读取——
> 如果你的站点存在 XSS 漏洞，令牌会被窃取。更严格的方案是把令牌放进 `httpOnly` Cookie
> （JS 读不到，但要多处理一层 CSRF 防护）。本书量级的练习项目，`localStorage` 足够；
> 真正的生产系统上线前，这是值得重新评估的一步。

---

## 9. 安全检查清单 + 进阶方向

上线前必须确认：

- [ ] `SECRET_KEY` 在 `.env` 里、够随机（`secrets.token_hex(32)`），绝不进 Git
- [ ] 生产环境全程 HTTPS（11 章讲过，令牌在 HTTP 明文下等于裸奔）
- [ ] 令牌有合理的过期时间（几小时到几天，不要"永不过期"）
- [ ] 登录/注册失败的错误信息不泄露"用户名是否存在"
- [ ] 密码最小长度（本章已加，`min_length=8`）
- [ ] 数据库里确认只有 `password_hash`，没有任何明文密码字段

**进阶方向**（本章不展开，知道名字即可）：

| 方向 | 关键词 |
|---|---|
| 令牌续期不用重新输密码 | Refresh Token（短期 access token + 长期 refresh token）|
| 防暴力破解登录 | 登录接口限流（Rate Limiting）|
| 不同用户不同权限 | 角色系统（role 字段 + 权限检查依赖）|
| 用 Google/GitHub 账号登录 | OAuth2 第三方登录（`authlib` 等库）|

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 登录接口返回 422 | 发了 JSON，接口要的是表单编码 | `Content-Type: application/x-www-form-urlencoded` + `URLSearchParams` |
| `Form data requires "python-multipart"` | 依赖没装 | `pip install python-multipart` |
| 重启服务后所有令牌都失效 | `SECRET_KEY` 每次启动随机生成 | 固定写进 `.env`，不要在代码里 `secrets.token_hex()` 现生成 |
| `/docs` 里 Authorize 按钮点了没用 | `tokenUrl` 和实际登录路径不一致 | `OAuth2PasswordBearer(tokenUrl="login")` 要对上真实路由路径 |
| 密码验证总是失败 | 哈希和验证用的不是同一个 `pwd_context` 配置 | 确保 hash/verify 用同一份 `CryptContext` 定义 |
| bcrypt 安装报错 | 系统缺编译工具 | 用 `passlib[bcrypt]` 而不是裸 `passlib`，会带上预编译依赖 |
| 401 但令牌看起来没过期 | 服务器和令牌里的时间不是同一时区 | 统一用 `datetime.utcnow()`，别混用本地时间 |
| 用户名重复没报错反而 500 | 忘了 catch `IntegrityError` | 参照第 4 节，`try/except sqlite3.IntegrityError` |

---

## 小练习

1. 完成 `users` 表 + 注册接口，验收：重复用户名返回 409、密码在数据库里是哈希不是明文。
2. 完成登录接口，用 `/docs` 或 curl（`-d "username=alice&password=xxx"`）拿到令牌。
3. 完成 `get_current_user` 依赖，挑一个你 demo 里的接口加上保护，
   验收：不带令牌返回 401，带对的令牌能访问，带篡改过的令牌也返回 401。
4. 前端实现登录表单 + token 存取，验证受保护接口在未登录时会被拒绝、登录后才能调通。
5. **（综合挑战，衔接 21~25 章）**：如果你想让音频工作台变成"只有登录后才能上传/合成/编排"的私人空间，
   把本章的 `get_current_user` 依赖加到 23、24、25 章的路由上——顺手给 `audios` 和 `clips` 表加一个
   `owner` 字段，让每个用户只能看到自己的素材和时间轴。这是本书全部知识第一次真正拼成"一个产品"。
