// 行为层（对应 docs/15、16 章）
// 运行前提：demo 后端已启动（uvicorn main:app --reload），然后双击打开 index.html 即可。
// 架构模式：改数据 → 重新拉取 → 整体重绘 —— 页面永远和数据库一致（docs/16 第 5 节）。

const API = "http://127.0.0.1:8000";      // 后端地址：只写这一处，好改

// ── 元素引用（docs/15 第 5 节）────────────────────────────
const listEl = document.querySelector("#todo-list");
const formEl = document.querySelector("#add-form");
const inputEl = document.querySelector("#new-title");
const countEl = document.querySelector("#count");
const errorEl = document.querySelector("#error-banner");

// ── 错误提示：页面内横幅，3 秒后自动消失 ─────────────────────
function showError(message) {
    errorEl.textContent = `操作失败：${message}`;
    errorEl.classList.remove("hidden");
    setTimeout(() => errorEl.classList.add("hidden"), 3000);
}

// ── 请求封装：统一处理两类错误（docs/16 第 3 节）──────────────
async function request(path, options = {}) {
    try {
        const response = await fetch(`${API}${path}`, options);
        // 防线 1：HTTP 层失败（404 / 422 / 500...）—— fetch 不会自动报错，必须查 ok
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${response.status}`);
        }
        // 204（删除成功）没有响应体，不能调 .json()
        return response.status === 204 ? null : await response.json();
    } catch (err) {
        // 防线 2：网络层失败（后端没启动、断网）也会落到这里
        showError(err.message);
        throw err;
    }
}

// ── 渲染：数据 → 页面（docs/16 第 5.2 节 ②）───────────────────
function renderTodos(todos) {
    listEl.innerHTML = "";                 // 清空重画（简单粗暴但够用）
    for (const todo of todos) {
        const li = document.createElement("li");
        li.className = "todo-row";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = todo.done;
        checkbox.addEventListener("change", () => toggleTodo(todo));

        const span = document.createElement("span");
        span.textContent = todo.title;     // 用户输入 → textContent（安全铁律）
        span.className = todo.done ? "title done" : "title";

        const delBtn = document.createElement("button");
        delBtn.textContent = "删除";
        delBtn.addEventListener("click", () => deleteTodo(todo.id));

        li.append(checkbox, span, delBtn);
        listEl.append(li);
    }
    const undone = todos.filter((t) => !t.done).length;
    countEl.textContent = `共 ${todos.length} 项，未完成 ${undone} 项`;
}

// ── 数据操作：每个函数 = 一次 API 调用 + 重新加载 ───────────────
async function loadTodos() {
    const todos = await request("/todos");
    renderTodos(todos);
}

async function addTodo(title) {
    await request("/todos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
    });
    await loadTodos();
}

async function toggleTodo(todo) {
    await request(`/todos/${todo.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ done: !todo.done }),   // 部分更新：只发 done
    });
    await loadTodos();
}

async function deleteTodo(id) {
    await request(`/todos/${id}`, { method: "DELETE" });
    await loadTodos();
}

// ── 事件绑定与启动（docs/16 第 5.2 节 ④）──────────────────────
formEl.addEventListener("submit", async (event) => {
    event.preventDefault();                // 拦住表单默认刷新（docs/15 第 6 节）
    const title = inputEl.value.trim();
    if (!title) return;                    // 空内容不提交
    await addTodo(title);
    inputEl.value = "";                    // 清空输入框
    inputEl.focus();
});

loadTodos();                               // 打开页面先加载一次
