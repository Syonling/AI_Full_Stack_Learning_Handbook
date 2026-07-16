# 17 · Vue 3 入门

> 前提：**16 章的原生版 Todo 必须亲手写完**。框架解决的是原生开发的痛点——没痛过，学框架就是背 API。
> 本章用 CDN 方式零配置入门 Vue 3，最后用它重写 Todo 页面，直观对比两种写法。
> 预计学习时间：4~5 小时。

---

## 学习目标

1. 理解框架到底解决什么问题（**数据驱动视图**）
2. 掌握 Vue 的响应式：`ref`、`reactive`、`computed`
3. 掌握核心指令：`v-if` / `v-for` / `v-bind` / `v-on` / `v-model`
4. 用 Vue 重写 16 章的 Todo 页面，体会代码量和心智负担的差异
5. 知道下一步的工程化路线（Vite / SFC / Router / Pinia 是什么）

---

## 1. 框架解决什么问题？

回顾 16 章的原生代码，你写了两类逻辑：

1. **数据操作**：调 API、更新 todos 数组 —— 这是业务本身
2. **DOM 同步**：createElement、append、textContent、classList…… —— 这是**把数据搬到页面上的体力活**

第 2 类占了一大半代码量，而且极易出 bug（忘了重绘、漏了解绑）。Vue 的核心思想：

```
原生：  数据变了 → 你手动改 DOM（renderTodos 整套体力活）
Vue：   数据变了 → 页面自动更新（你只声明"页面长什么样"）
```

这叫**声明式渲染 + 响应式数据**。你从"指挥浏览器一步步画"变成"描述结果，剩下的交给框架"。

---

## 2. 零配置起步：CDN 引入

不需要 npm、不需要构建——一个 HTML 文件就能学 Vue：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Vue 起步</title>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
</head>
<body>
    <!-- Vue 接管这个 div 内部的一切 -->
    <div id="app">
        <h1>{{ message }}</h1>                    <!-- 插值：把数据渲染进页面 -->
        <button @click="count++">点了 {{ count }} 次</button>
    </div>

    <script>
        const { createApp, ref } = Vue;

        createApp({
            setup() {
                const message = ref("Hello, Vue!");   // ref() 把值变成"响应式"
                const count = ref(0);
                return { message, count };            // return 的东西模板里才能用
            },
        }).mount("#app");                             // 挂载到 #app
    </script>
</body>
</html>
```

跑起来点几下按钮——**你没有写任何 DOM 操作代码**，页面自己更新了。这就是响应式。

> **要点**：`ref(0)` 返回的是一个包装对象。**JS 代码里**读写要用 `.value`（`count.value++`），
> **模板里**不用（直接 `{{ count }}`）。这是 Vue 新手第一大坑，现在记住它。

---

## 3. 响应式三件套

```javascript
const { ref, reactive, computed } = Vue;

// ref：包装单个值（数字、字符串、布尔、数组都行）
const count = ref(0);
count.value++;

// reactive：包装对象（不需要 .value，直接点出属性）
const user = reactive({ name: "Alice", age: 25 });
user.age++;

// computed：由其他响应式数据"算出来"的值，依赖变了自动重算
const todos = ref([
    { id: 1, title: "learn vue", done: false },
    { id: 2, title: "learn vite", done: true },
]);
const undoneCount = computed(() =>
    todos.value.filter((t) => !t.done).length
);
// 模板里用 {{ undoneCount }}，todos 一变它自动跟着变——
// 16 章里每次手动更新 countEl.textContent 的活，没了
```

新手期的简单取舍：**单值用 ref，对象用 reactive，"统计/派生"用 computed**。拿不准就全用 ref。

---

## 4. 核心指令：模板里的魔法属性

指令 = 写在 HTML 标签上的 `v-` 前缀属性，是 Vue 声明式的核心词汇。

```html
<div id="app">
    <!-- v-if / v-else：条件渲染 -->
    <p v-if="todos.length === 0">暂无待办 🎉</p>
    <ul v-else>
        <!-- v-for：列表渲染（:key 帮 Vue 识别谁是谁，必写）-->
        <li v-for="todo in todos" :key="todo.id">
            {{ todo.title }}
        </li>
    </ul>

    <!-- v-bind：动态属性，简写冒号 : -->
    <span :class="todo.done ? 'done' : ''">...</span>
    <img :src="imageUrl">

    <!-- v-on：事件监听，简写 @ -->
    <button @click="addTodo">添加</button>
    <input @keyup.enter="addTodo">           <!-- 修饰符：回车才触发 -->

    <!-- v-model：双向绑定（输入框 ⇄ 变量自动同步，取代 .value 读写）-->
    <input v-model="newTitle" placeholder="要做什么？">
</div>
```

对照 15/16 章的原生写法：

| 原生 JS | Vue |
|---|---|
| `el.addEventListener("click", fn)` | `@click="fn"` |
| `inputEl.value` 读 + `input` 事件监听 | `v-model="newTitle"` 一行搞定 |
| `createElement` + 循环 + `append` | `v-for` |
| `el.classList.add/remove` | `:class="条件表达式"` |
| `renderTodos()` 手动重绘 | 不存在，数据变了自动更新 |

---

## 5. 实战：Vue 版 Todo（对比 16 章）

同一个后端（demo 的 Todo API），完整的 Vue 实现——注意**完全没有 DOM 操作**：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Todo (Vue 版)</title>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        body { font-family: sans-serif; max-width: 520px; margin: 40px auto; }
        .done { text-decoration: line-through; color: #999; }
        li { display: flex; gap: 8px; align-items: center; padding: 6px 0; }
        li span { flex: 1; }
    </style>
</head>
<body>
<div id="app">
    <h1>Todo List</h1>

    <form @submit.prevent="addTodo">          <!-- .prevent = event.preventDefault() -->
        <input v-model="newTitle" placeholder="要做什么？">
        <button>添加</button>
    </form>

    <p v-if="todos.length === 0">暂无待办 🎉</p>
    <ul v-else>
        <li v-for="todo in todos" :key="todo.id">
            <input type="checkbox" :checked="todo.done" @change="toggleTodo(todo)">
            <span :class="{ done: todo.done }">{{ todo.title }}</span>
            <button @click="deleteTodo(todo.id)">删除</button>
        </li>
    </ul>

    <p>共 {{ todos.length }} 项，未完成 {{ undoneCount }} 项</p>
</div>

<script>
    const { createApp, ref, computed, onMounted } = Vue;
    const API = "http://127.0.0.1:8000";

    createApp({
        setup() {
            const todos = ref([]);
            const newTitle = ref("");
            const undoneCount = computed(() => todos.value.filter(t => !t.done).length);

            // 数据操作逻辑和 16 章几乎一样——变的只是"渲染"消失了
            async function loadTodos() {
                const res = await fetch(`${API}/todos`);
                todos.value = await res.json();   // 赋值即更新页面
            }
            async function addTodo() {
                const title = newTitle.value.trim();
                if (!title) return;
                await fetch(`${API}/todos`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ title }),
                });
                newTitle.value = "";
                await loadTodos();
            }
            async function toggleTodo(todo) {
                await fetch(`${API}/todos/${todo.id}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ done: !todo.done }),
                });
                await loadTodos();
            }
            async function deleteTodo(id) {
                await fetch(`${API}/todos/${id}`, { method: "DELETE" });
                await loadTodos();
            }

            onMounted(loadTodos);    // 组件挂载完成后执行 ≈ 16 章末尾那句 loadTodos()

            return { todos, newTitle, undoneCount, addTodo, toggleTodo, deleteTodo };
        },
    }).mount("#app");
</script>
</body>
</html>
```

对比结论：**API 调用逻辑一行没少**（这部分是业务，框架替代不了），
但 16 章 `renderTodos` 那 25 行 DOM 体力活**整体消失**，换成了模板里的声明。
页面越复杂，这笔账差距越大——这就是框架存在的意义。

---

## 6. 下一步：工程化路线（先认名词）

CDN 方式适合学习；真实 Vue 项目用**构建工具**组织，几个必然遇到的名词：

| 名词 | 是什么 | 类比你学过的 |
|---|---|---|
| **Vite** | 官方构建工具，`npm create vue@latest` 一键创建项目 | 前端界的 uvicorn + venv |
| **SFC**（.vue 单文件组件）| 一个文件装一个组件的模板+逻辑+样式 | 后端按职责拆文件（07 章）|
| **组件** | 可复用的页面积木（`<TodoItem>` 用在任何地方）| 函数之于代码 |
| **Vue Router** | 前端路由：单页应用里切换"页面" | FastAPI 的路由概念搬到前端 |
| **Pinia** | 全局状态管理：跨组件共享数据 | 全局的 settings 对象（08 章）|

顺便揭个底：**你的文档网站 VitePress = Vite + Vue**——学到这里，你已经有能力给自己的网站写自定义 Vue 组件了。

学习资源：[Vue 官方中文教程](https://cn.vuejs.org/tutorial/)（互动式，质量极高，本章之后直接接得上）。

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 页面显示 `{{ message }}` 原文 | Vue 没加载成功 / mount 的选择器不对 | F12 看 CDN 请求是否成功；确认 `#app` 存在 |
| JS 里改了 ref 页面没反应 | 忘了 `.value`（`count++` 而不是 `count.value++`）| ref 在 JS 里必须 .value |
| 模板里报 `xxx is not defined` | setup 里忘了 return | 模板要用的都得 return |
| v-for 控制台警告 key | 没写 `:key` | 加 `:key="todo.id"` |
| 输入框内容拿不到 | 混用了 v-model 和 .value 读 DOM | 用了 v-model 就只操作变量 |
| @submit 后页面刷新 | 忘了 `.prevent` 修饰符 | `@submit.prevent="fn"` |
| 样式类没生效 | `:class` 对象语法写错 | `:class="{ done: todo.done }"`（类名: 条件）|

---

## 小练习

1. 把第 2 节的计数器例子加一个 `computed`：显示"是偶数/是奇数"。
2. 抄写（别复制）第 5 节的 Vue 版 Todo 跑起来，然后给它加 16 章练习 1 的"只看未完成"过滤（提示：再来一个 `computed`）。
3. 对照实验：在 Vue 版里故意把 `todos.value = await res.json()` 改成普通变量赋值，观察页面为什么不更新——理解响应式的边界。
4. 用官方脚手架 `npm create vue@latest` 建一个工程化项目，把你的 Todo 迁移成 `.vue` 单文件组件（这是通往真实 Vue 开发的门）。
5. **毕业挑战**：用 Vue 重写你的 Audio Book 前端（main.html），后端用你在 16 章练习 4 写的 `/story` 接口。

> 🎓 前端三件套 + Vue 的地基到此打完：**HTML/CSS/JS → Vue** 负责用户看到的一切，
> **FastAPI + SQLite** 负责数据与逻辑，**Git + Docker** 负责交付上线。
> 但先别合上书——同组还有两堂"功力课"：[18 · 前端工程组织](18-frontend-engineering.md)
> 和 [19 · 设计美学：Apple 风格](19-apple-design.md)；然后从 [21 章](21-audio-overview.md) 起，
> 把这一切组装成一个真正的音频产品。
