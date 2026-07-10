# 15 · JavaScript 基础

> JS 负责**行为**：响应点击、修改页面、和后端通信。你已经会 Python 了——本章大量用 Python 对照讲解，你会学得非常快。
> 预计学习时间：3~4 小时。需要第 13 章 HTML；建议已学完 01 章 Python 基础。

---

## 学习目标

1. 会在页面中引入并运行 JS
2. 掌握变量、函数、数组、对象——并知道和 Python 的对应关系
3. 会操作 DOM：查找元素、改内容、改样式、增删节点
4. 会监听事件（点击、输入、提交）
5. 能完整看懂你的 main.html 里那段 `<script>`

---

## 1. 在哪里写 JS

```html
<!-- 方式 1：外部文件（✅ 正式做法）。defer = 等 HTML 解析完再执行 -->
<head>
    <script src="app.js" defer></script>
</head>

<!-- 方式 2：<script> 标签放在 </body> 前（你的 main.html 是这种，效果同 defer）-->
<body>
    ...页面内容...
    <script>
        console.log("Hello, JS!");
    </script>
</body>
```

`console.log` 是 JS 的 `print`——输出在 **F12 的 Console 面板**里。
Console 还是一个交互式解释器（相当于 Python 的 REPL），可以直接敲代码试验。

> **要点**：为什么要 `defer` 或放底部？JS 如果在 HTML 之前执行，`document.getElementById(...)`
> 会因为元素还不存在而拿到 `null`——这是新手第一大坑。

---

## 2. 变量与类型（Python 对照速成）

```javascript
// 声明变量：const 不可重新赋值（默认首选），let 可以。别用 var（老语法，有坑）
const name = "Alice";
let count = 0;
count = count + 1;      // let 可以重新赋值

// 模板字符串：反引号 ` 包裹，${} 嵌入变量 —— 相当于 Python 的 f-string
const msg = `user ${name} has ${count} todos`;

// 基本类型
const n = 42;           // number（JS 不分 int/float）
const ok = true;        // boolean（小写！Python 是 True）
const nothing = null;   // 主动表示"空"（类似 None）
let x;                  // undefined：声明了但没赋值
```

| Python | JavaScript |
|---|---|
| `name = "a"` | `const name = "a";` |
| `f"hi {name}"` | `` `hi ${name}` `` |
| `True / False / None` | `true / false / null` |
| `print(x)` | `console.log(x)` |
| `# 注释` | `// 注释` 或 `/* 多行 */` |
| 缩进定代码块 | `{ }` 定代码块，缩进只为美观 |

**比较必须用三等号**：`===`（等于）和 `!==`（不等于）。
双等号 `==` 会做隐式类型转换（`"1" == 1` 竟然是 true），永远别用。

```javascript
if (count === 0) {
    console.log("empty");
} else if (count > 10) {
    console.log("a lot");
} else {
    console.log("some");
}
```

---

## 3. 函数

```javascript
// 普通函数声明
function greet(name) {
    return `Hello, ${name}!`;
}

// 箭头函数（现代 JS 主流写法，尤其做回调时）
const greet2 = (name) => {
    return `Hello, ${name}!`;
};

// 箭头函数简写：只有一条 return 时，可省略 {} 和 return
const greet3 = (name) => `Hello, ${name}!`;
const double = (n) => n * 2;
```

三种写法功能基本等价，先都能看懂，自己写时用哪种都行。
箭头函数大量出现在"把函数当参数传"的场景——下一节马上见到。

---

## 4. 数组与对象（对照 list 和 dict）

```javascript
// 数组 ≈ Python list
const todos = ["learn html", "learn css", "learn js"];
todos.push("learn vue");        // ≈ append
todos.length;                   // ≈ len(todos)
todos[0];                       // 索引访问相同

// 遍历
for (const t of todos) {        // ≈ for t in todos（注意是 of 不是 in！）
    console.log(t);
}

// 对象 ≈ Python dict（但键不用加引号，访问用点号）
const todo = { id: 1, title: "learn js", done: false };
todo.title;                     // 读取 ≈ todo["title"]（JS 两种都行，点号更常用）
todo.done = true;               // 修改
```

### 三个必会的数组方法（≈ 列表推导式）

```javascript
const todos = [
    { id: 1, title: "learn html", done: true },
    { id: 2, title: "learn js", done: false },
];

// map：逐个转换 ≈ [t["title"] for t in todos]
const titles = todos.map((t) => t.title);

// filter：条件过滤 ≈ [t for t in todos if not t["done"]]
const undone = todos.filter((t) => !t.done);

// find：找第一个匹配 ≈ next((t for t in todos if t["id"] === 2), None)
const target = todos.find((t) => t.id === 2);   // 找不到返回 undefined
```

注意这个模式：**`map(箭头函数)`——把函数作为参数传进去**。
你的 main.html 里 `data.map(item => item.text).join("\n")` 就是它：提取每条的 text，再用换行拼起来。

---

## 5. DOM：用 JS 操控页面

DOM（Document Object Model）= 浏览器把 HTML 解析成的**对象树**，JS 通过它读写页面。

### 5.1 查找元素

```javascript
// 现代首选：querySelector，参数就是 CSS 选择器（14 章白学了吗！）
const btn = document.querySelector("#submitButton");   // 按 id 找
const card = document.querySelector(".card");          // 按 class 找第一个
const items = document.querySelectorAll("li");         // 找全部（可遍历）

// 老写法（你的 main.html 用的这种，效果一样）
const btn2 = document.getElementById("submitButton");
```

### 5.2 读写内容与样式

```javascript
const output = document.querySelector("#outputText");

output.textContent = "纯文本，最安全";        // 内容会被原样显示
output.innerHTML = "<b>能解析 HTML 标签</b>";  // ⚠️ 别把用户输入放进来（XSS 攻击入口）

const input = document.querySelector("#inputText");
input.value;                                  // 表单元素取值用 .value 不是 textContent！

// 改样式：优先用 classList 切换预先写好的 CSS 类（样式归 CSS 管）
output.classList.add("highlight");
output.classList.remove("highlight");
output.classList.toggle("dark");              // 有则删、无则加
```

### 5.3 创建与删除元素

```javascript
const li = document.createElement("li");      // 创建
li.textContent = "new todo";
document.querySelector("ul").append(li);      // 挂到页面上（不挂就看不见）

li.remove();                                  // 删除
```

> **要点**：安全铁律——**显示用户输入的内容一律用 `textContent`**。
> `innerHTML` 只用于插入你自己写死的模板。

---

## 6. 事件：让页面响应操作

```javascript
const btn = document.querySelector("#submitButton");

// addEventListener(事件名, 触发时执行的函数)
btn.addEventListener("click", () => {
    console.log("clicked!");
});

// 输入框实时监听（handbook 的搜索就是这个原理）
const search = document.querySelector("#search");
search.addEventListener("input", () => {
    console.log("当前内容:", search.value);
});

// 表单提交：必须阻止默认的"提交并刷新页面"行为
const form = document.querySelector("#signup");
form.addEventListener("submit", (event) => {
    event.preventDefault();          // ← 拦下浏览器默认动作，改由 JS 接管
    console.log("由 JS 处理提交");
});
```

常用事件：`click`、`input`（每敲一个字）、`change`（值改完失焦后）、`submit`、`keydown`。

---

## 7. 综合解读：你的 main.html 脚本

现在逐行看懂它（简化注释版）：

```javascript
const inputText = document.getElementById('inputText');     // 5.1 查找元素
const outputText = document.getElementById('outputText');
const submitButton = document.getElementById('submitButton');

submitButton.addEventListener('click', async () => {        // 6. 监听点击
    const input = inputText.value;                           // 5.2 表单取值

    const response = await fetch("/story", {                 // ← 16 章的主角：发请求
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: input }),
    });
    const data = await response.json();
    outputText.textContent = data.message;                   // 5.2 写回页面
});
```

只剩 `fetch / async / await / JSON` 四个概念没讲——它们就是下一章的全部内容。

---

## 8. 三件后面必用的散装武器

这三样在音频项目章节（21~25）里高频出现，提前备好：

### 8.1 定时器：setTimeout / setInterval

```javascript
// setTimeout：N 毫秒后执行一次（"稍后做一件事"）
const id1 = setTimeout(() => {
    banner.classList.add("hidden");     // 3 秒后自动隐藏提示条
}, 3000);

// setInterval：每 N 毫秒执行一次（轮询、时钟、调度都是它）
const id2 = setInterval(() => {
    console.log("每秒问一次：好了吗？");
}, 1000);

// ★ 铁律：开了就要有人负责关，否则永远跑下去（内存泄漏 + 疯狂请求）
clearTimeout(id1);
clearInterval(id2);
```

记住这个模式——**"开定时器时就想好谁来 clear 它"**。24 章的轮询、25 章的播放调度器
全靠 setInterval，而它们的 bug 也几乎全是"忘了 clear"。

### 8.2 展开运算符 `...`

把数组/对象"摊开"：

```javascript
const nums = [3, 7, 2];
Math.max(...nums);              // 等于 Math.max(3, 7, 2) → 7
const copy = [...nums];         // 浅拷贝一份数组
const merged = [...a, ...b];    // 合并两个数组

const todo = { id: 1, title: "learn" };
const updated = { ...todo, done: true };   // 复制对象并覆盖某字段（很常用）
```

### 8.3 解构赋值

从对象/数组里"按名提取"，少写一堆 `xxx.yyy`：

```javascript
const clip = { audio_id: 3, start_seconds: 4.5, duration: 10 };

const { audio_id, duration } = clip;       // 一次取出两个字段
console.log(audio_id, duration);           // 3 10

// 函数参数直接解构（回调里特别顺手）
const summarize = ({ audio_id, duration }) => `#${audio_id}: ${duration}s`;

// 数组解构
const [first, second] = ["a", "b", "c"];   // first="a", second="b"
```

> **要点**：`{ ...todo, done: true }` 和 `({ a, b }) => ...` 这两个写法
> 在现代 JS 代码里出现率极高——即使自己先不写，也必须能一眼读懂。

---

## 常见错误与排查

| 报错/现象 | 原因 | 解决 |
|---|---|---|
| `Cannot read properties of null (reading 'addEventListener')` | JS 执行时元素还不存在，或选择器拼错 | script 加 `defer` 或放 body 底部；检查选择器 |
| `xxx is not defined` | 变量名拼错 / 忘了声明 | 看报错行号，检查拼写 |
| `Assignment to constant variable` | 给 const 重新赋值 | 需要变的量用 `let` |
| 取输入框内容是空的 | 用了 `.textContent` | 表单元素用 `.value` |
| `"1" == 1` 为 true 导致逻辑怪异 | 用了双等号 | 永远用 `===` / `!==` |
| for...in 遍历数组拿到的是索引字符串 | in 和 of 搞混 | 遍历数组用 `for...of` |
| 点提交按钮页面刷新，什么都没发生 | 表单默认提交行为 | `event.preventDefault()` |

调试三板斧：`console.log` 大法 → F12 Console 看报错（红字，从上往下第一条最重要）→ Sources 面板打断点（和 03 章 VSCode 调试同理）。

---

## 小练习

1. 计数器：页面放一个数字和 `+1`、`-1`、`归零` 三个按钮，用 JS 实现（练变量 + 事件 + textContent）。
2. 待办列表（纯前端版）：一个输入框 + 添加按钮，点击后把内容 `createElement` 成 `<li>` 挂到列表上；每个 li 再挂一个删除按钮（练 DOM 增删）。
3. 实时过滤：给第 2 题加一个搜索框，`input` 事件里用 `filter` + `classList` 隐藏不匹配的项（这就是 handbook 搜索的迷你版）。
4. 用 Console 面板直接操作你的文档网站：`document.querySelectorAll("h2").length` 数数当前页有几个二级标题。

> 下一章：[16 · JS 网络与联调](16-js-network-and-integration.md) —— fetch + async/await，前端连上你的 FastAPI！
