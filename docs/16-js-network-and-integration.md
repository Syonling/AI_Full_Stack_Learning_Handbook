# 16 · JS 网络与联调：fetch + 前后端打通

> 本章是前端部分的**实战核心**：学会 fetch 和 async/await，然后给你的 Todo API 写一个完整的前端页面。
> 页面代码与 [demo/frontend/](../demo/frontend/) **逐行对应**，建议边读边跑。
> 预计学习时间：4~5 小时。需要 13~15 章 + 后端 07 章（demo API 要能跑起来）。

---

## 学习目标

1. 理解 fetch 的工作方式和 `async / await`
2. 会发 GET / POST / PUT / DELETE 四种请求（正好对上你的 CRUD API）
3. 会处理 JSON、检查响应状态、捕获错误
4. 会用 DevTools 的 **Network 面板**调试前后端联调
5. 完成一个真正的全栈闭环：浏览器页面 ⇄ FastAPI ⇄ SQLite

---

## 1. fetch：浏览器里的 HTTP 客户端

`fetch` 就是浏览器版的 curl（10 章用过的那个），发请求、拿响应：

```javascript
// 最简 GET 请求
const response = await fetch("http://127.0.0.1:8000/todos");
const todos = await response.json();     // 把响应体解析成 JS 数组/对象
console.log(todos);
```

### 为什么有两个 await？

网络请求需要时间（几十毫秒到几秒），JS 不会傻等——`fetch` 返回的是一个 **Promise**（"未来会有结果的凭据"）。
`await` 的意思是"等这个凭据兑现再继续下一行"：

- 第一个 `await fetch(...)`：等**响应头**到达
- 第二个 `await response.json()`：等**响应体**下载并解析完

规则和 Python 一样：**用了 `await` 的函数必须声明为 `async`**（01 章讲过的知识原样迁移）：

```javascript
async function loadTodos() {
    const response = await fetch("http://127.0.0.1:8000/todos");
    const todos = await response.json();
    return todos;
}
```

---

## 2. 四种请求：对上你的 CRUD API

还记得 07 章的接口表吗？前端全部对号入座：

```javascript
const API = "http://127.0.0.1:8000";

// GET：读取（fetch 默认就是 GET）
const todos = await (await fetch(`${API}/todos`)).json();

// POST：新建 —— 三件套：method + headers + body
const created = await fetch(`${API}/todos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },   // 告诉后端"我发的是 JSON"
    body: JSON.stringify({ title: "learn fetch" }),    // JS 对象 → JSON 字符串
});

// PUT：更新（部分更新，只发想改的字段——还记得 TodoUpdate 吗）
await fetch(`${API}/todos/1`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ done: true }),
});

// DELETE：删除（无 body）
await fetch(`${API}/todos/1`, { method: "DELETE" });
```

### JSON 的两个转换函数

| 函数 | 方向 | Python 对应 |
|---|---|---|
| `JSON.stringify(obj)` | JS 对象 → JSON 字符串（发出去前）| `json.dumps` |
| `response.json()` | JSON 响应 → JS 对象（收进来后）| `json.loads` |

---

## 3. 错误处理：两类错误，两道防线

**fetch 有个反直觉的行为**：后端返回 404/500 时它**不报错**——只有网络本身断了才报错。
所以必须两道防线都设：

```javascript
async function createTodo(title) {
    try {
        const response = await fetch(`${API}/todos`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title }),
        });

        // 防线 1：HTTP 层面的失败（404 / 422 / 500...）
        if (!response.ok) {                    // ok = 状态码在 200~299
            const err = await response.json(); // FastAPI 的错误响应带 detail
            throw new Error(err.detail || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (err) {
        // 防线 2：网络失败（后端没启动、断网）也会落到这里
        console.error("createTodo failed:", err);
        alert(`操作失败：${err.message}`);      // 实际项目用页面内提示代替 alert
        return null;
    }
}
```

> **要点**：`!response.ok` 检查是新手最容易漏的——漏了它，后端返回 422 时
> 你的代码会把错误信息当正常数据渲染，出现各种诡异的 undefined。

---

## 4. Network 面板：联调的眼睛

F12 → **Network（网络）** 标签页，刷新页面后你能看到每一个请求：

| 看什么 | 在哪看 | 判断什么 |
|---|---|---|
| 请求发出去了吗 | 列表里有没有这条 | JS 是否执行到了 fetch |
| 发到哪、方法对吗 | 点开 → Headers | URL 拼错？POST 写成 GET？ |
| 发的数据对吗 | 点开 → Payload | body 的 JSON 长什么样 |
| 后端回了什么 | 点开 → Response | 状态码 + 响应体（422 的 detail 就在这）|
| 是不是 CORS 问题 | Console 的红色报错 | 提到 "blocked by CORS policy" 就是 |

**前后端联调的黄金分界法**：Network 里请求的 Payload 是对的，但 Response 是错的 → **后端的锅**（去看 uvicorn 日志）；
请求根本没发出、URL/Payload 不对 → **前端的锅**。一分钟定位问题在哪边。

---

## 5. 实战：给 Todo API 写完整前端

目标效果：输入框添加待办 → 列表展示 → 复选框切换完成 → 删除按钮删掉，全部实时同步到 SQLite。
代码在 [demo/frontend/](../demo/frontend/)，三个文件各司其职（13~15 章的知识各归各位）：

```
demo/frontend/
├── index.html    # 结构（13 章）
├── style.css     # 样式（14 章）
└── app.js        # 行为（15 章 + 本章）
```

### 5.1 运行方式

```bash
# 终端 1：启动后端（07 章的老朋友）
cd demo && source .venv/bin/activate && cd app
uvicorn main:app --reload

# 然后直接双击打开 demo/frontend/index.html 即可
# （能直接打开是因为 demo 的 CORS 配了 allow_origins=["*"]，06 章讲过）
```

### 5.2 app.js 核心逻辑逐块讲解

**① 状态与元素引用**

```javascript
const API = "http://127.0.0.1:8000";        // 后端地址：只写这一处，好改

const listEl = document.querySelector("#todo-list");
const formEl = document.querySelector("#add-form");
const inputEl = document.querySelector("#new-title");
const countEl = document.querySelector("#count");
```

**② 渲染函数：数据 → 页面（单向）**

```javascript
function renderTodos(todos) {
    listEl.innerHTML = "";                   // 清空重画（简单粗暴但够用）
    for (const todo of todos) {
        const li = document.createElement("li");
        li.className = "todo-row";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = todo.done;
        checkbox.addEventListener("change", () => toggleTodo(todo));

        const span = document.createElement("span");
        span.textContent = todo.title;       // 用户输入 → textContent（15 章安全铁律）
        span.className = todo.done ? "title done" : "title";

        const delBtn = document.createElement("button");
        delBtn.textContent = "删除";
        delBtn.addEventListener("click", () => deleteTodo(todo.id));

        li.append(checkbox, span, delBtn);
        listEl.append(li);
    }
    countEl.textContent = `共 ${todos.length} 项，未完成 ${todos.filter(t => !t.done).length} 项`;
}
```

**③ 数据操作：每个函数 = 一次 API 调用 + 重新加载**

```javascript
async function loadTodos() {
    const response = await fetch(`${API}/todos`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    renderTodos(await response.json());
}

async function addTodo(title) {
    await fetch(`${API}/todos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
    });
    await loadTodos();                       // 改完重新拉取 → 页面永远和数据库一致
}

async function toggleTodo(todo) {
    await fetch(`${API}/todos/${todo.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ done: !todo.done }),   // 部分更新：只发 done
    });
    await loadTodos();
}

async function deleteTodo(id) {
    await fetch(`${API}/todos/${id}`, { method: "DELETE" });
    await loadTodos();
}
```

**④ 事件绑定与启动**

```javascript
formEl.addEventListener("submit", async (event) => {
    event.preventDefault();                  // 拦住表单默认刷新（15 章）
    const title = inputEl.value.trim();
    if (!title) return;                      // 空内容不提交
    await addTodo(title);
    inputEl.value = "";                      // 清空输入框
});

loadTodos();                                 // 打开页面先加载一次
```

注意这个架构：**"改数据 → 重新拉取 → 整体重绘"**。它不是性能最优的，但逻辑最简单、
永远不会出现"页面和数据库对不上"。等你以后觉得"每次全量重绘好浪费"时——恭喜，你已经理解了 Vue/React 要解决的问题（17 章见）。

### 5.3 验收清单（务必逐项跑一遍）

- [ ] 添加一条待办 → 列表出现，**刷新页面后还在**（存进 SQLite 了）
- [ ] 勾选复选框 → 标题出现删除线；去 `/docs` 里 GET 一下确认 done 变了
- [ ] 删除一条 → 列表消失；uvicorn 日志里有一条 DELETE 记录
- [ ] **关掉后端**再添加 → 打开 Console 和 Network，观察失败长什么样
- [ ] 在 Network 面板点开一条 POST 请求，找到 Payload 和 Response

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| Console 报 CORS 错误 | 后端没配跨域 | demo 已配好；自己的项目照 06 章加 CORSMiddleware |
| `Failed to fetch` | 后端没启动 / 端口不对 | 确认 uvicorn 在跑、API 常量端口一致 |
| 发 POST 后端收到 422 | 忘了 Content-Type 头 / body 没 stringify | 检查三件套齐不齐 |
| 页面数据永远是旧的 | 改完没重新 loadTodos | 每个写操作后调 loadTodos() |
| `[object Object]` 显示在页面上 | 把对象直接塞给 textContent | 先取字段：`data.title`，或 `JSON.stringify(data)` 调试 |
| await 报语法错 | 所在函数没标 async | 外层函数加 `async` |
| 复选框点了没反应 | 监听了 click 但浏览器行为吞掉 / 忘绑定 | checkbox 用 `change` 事件 |

---

## 小练习（扩展 demo/frontend）

1. 加"只看未完成"过滤按钮（提示：GET `/todos?done=false`，07 章的查询参数终于被前端用上了）。
2. 把 `alert` 错误提示改成页面顶部的红色横幅 div，3 秒后自动消失（`setTimeout`）。
3. 双击标题进入编辑模式，改完回车发 PUT 更新 title（提示：`dblclick` 事件 + 临时替换成 input）。
4. **终极练习**：现在你拥有了实现 Audio Book 的全部知识——去把 [Backend/main.py](../demo/) 的 `/story` 接口写出来，让你自己的 main.html 真正跑起来。这是整个学习系统给你准备的毕业设计。

> 下一章：[17 · Vue 3 入门](17-vue-basics.md) —— 体验框架如何把本章 100 行 DOM 代码变成 30 行。
