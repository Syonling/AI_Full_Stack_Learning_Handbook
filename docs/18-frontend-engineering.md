# 18 · 前端工程组织：让代码优雅清晰

> 能跑的代码和优雅的代码之间，差的就是本章：文件怎么分、样式怎么管、命名怎么起。
> 这些决定了三个月后的你还能不能看懂今天的代码。
> 预计学习时间：3~4 小时。需要 13~16 章；末节涉及 17 章的 Vue。

---

## 学习目标

1. 掌握前端项目的标准文件夹结构（可直接套用的模板）
2. 会用 **CSS 变量（设计令牌）** 集中管理颜色、间距、字号
3. 会用简化版 **BEM** 命名，告别 `.div2` 和 `.newnew`
4. 会用 **ES Modules** 把 JS 按职责拆分成多个文件
5. 知道这套原则在 Vue 项目里如何对应

---

## 1. 为什么"组织"值得专门学一章

代码质量的分水岭不在"会不会写"，而在**改起来痛不痛**：

| 没有组织的项目 | 有组织的项目 |
|---|---|
| 想改主题色，全局搜索替换 47 处 `#2563eb` | 改一行 CSS 变量 |
| 想找"删除按钮的样式"，在 800 行的 style.css 里滚动翻找 | 直接打开 `components.css` |
| 改了一个函数，不知道会不会弄坏别处 | 每个文件职责单一，影响范围清晰 |

原则只有一条，后面全是它的推论：**相关的放一起，无关的分开（高内聚，低耦合）**。

---

## 2. 标准文件夹结构（模板，直接套用）

demo/frontend 的三文件结构（HTML/CSS/JS 分家）是起点。页面多起来之后的标准形态：

```
frontend/
├── index.html
├── css/
│   ├── base.css          # 全局基调：reset、变量、body 字体（改动最少）
│   ├── layout.css        # 骨架布局：容器、导航、页脚、栅格
│   └── components.css    # 组件样式：按钮、卡片、表单、列表（改动最多）
├── js/
│   ├── api.js            # 只管和后端通信（所有 fetch 都在这）
│   ├── ui.js             # 只管渲染和 DOM 操作
│   └── main.js           # 入口：事件绑定，把 api 和 ui 串起来
└── assets/
    ├── images/
    └── fonts/
```

```html
<!-- index.html 里按"基调 → 布局 → 组件"的顺序引入 -->
<link rel="stylesheet" href="css/base.css">
<link rel="stylesheet" href="css/layout.css">
<link rel="stylesheet" href="css/components.css">
<script src="js/main.js" type="module" defer></script>
```

分层的判断标准：**"这条样式如果删掉，影响的是整个站、页面骨架、还是某一个部件？"** 答案就是它该在的文件。

> **要点**：不要一开始就建齐所有文件夹。单页面用三文件；文件超过 ~200 行再拆层——
> **结构跟着复杂度走，而不是提前设计**（和 10 章"阶段二够用"是同一个道理）。

---

## 3. CSS 变量：设计令牌（本章最重要的一节）

**设计令牌（Design Token）= 把所有"设计决策"提取成有名字的变量，集中定义、全局引用。**

```css
/* base.css —— 全站唯一的"设计决策清单" */
:root {
    /* 色彩 */
    --color-bg: #f6f7f9;
    --color-surface: #ffffff;      /* 卡片等表面 */
    --color-text: #333333;
    --color-text-muted: #888888;
    --color-accent: #2563eb;       /* 全站唯一强调色 */
    --color-danger: #ef4444;

    /* 间距（只允许用这几档，杜绝随手写 13px）*/
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 40px;

    /* 圆角与阴影 */
    --radius-md: 10px;
    --shadow-sm: 0 1px 3px rgb(0 0 0 / 0.08);

    /* 字号 */
    --text-sm: 14px;
    --text-md: 16px;
    --text-lg: 20px;
}
```

```css
/* components.css —— 只引用令牌，不出现具体数值 */
.card {
    background: var(--color-surface);
    padding: var(--space-md);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
}
.btn-primary {
    background: var(--color-accent);
    padding: var(--space-sm) var(--space-md);
}
```

三个立竿见影的收益：

1. **改主题 = 改一处**：想换强调色，只改 `--color-accent` 一行
2. **深色模式几乎免费**：只需在媒体查询里覆盖变量，组件代码一行不动

   ```css
   @media (prefers-color-scheme: dark) {
       :root {
           --color-bg: #12151a;
           --color-surface: #1b2028;
           --color-text: #e8ebef;
       }
   }
   ```

3. **强制一致性**：间距只有 5 档可选，页面自然整齐（这也是 19 章 Apple 风格的地基）

> **要点**：判断 CSS 写得好不好的一个速查法——`components.css` 里**搜不到 `#` 开头的颜色值**，
> 全是 `var(--...)`，就说明令牌化做对了。

---

## 4. 命名规范：简化版 BEM

CSS 类名混乱是项目腐化最快的地方。BEM（Block__Element--Modifier）的简化版足够你用两年：

```css
/* Block：独立组件，名词 */
.card { }
.todo-row { }

/* Element：组件内部的零件，双下划线 */
.card__title { }
.card__footer { }
.todo-row__checkbox { }

/* Modifier：状态或变体，双横线 */
.card--featured { }
.btn--danger { }
.todo-row--done { }
```

```html
<li class="todo-row todo-row--done">
    <input class="todo-row__checkbox" type="checkbox">
    <span class="todo-row__title">learn BEM</span>
</li>
```

配套的两条命名铁律：

- **语义命名，不要表现命名**：`.btn--danger` ✅（说明"是什么"）；`.red-button` ❌（哪天危险色改成橙色就尴尬了）
- **JS 钩子和样式类分离**：给 JS 用的选择器加 `js-` 前缀或用 `data-` 属性（`.js-delete-btn`），
  这样改样式类名永远不会弄断 JS

---

## 5. JS 模块化：ES Modules

一个 `app.js` 超过 ~150 行就该拆了。现代 JS 的拆分机制是 **ES Modules**——`export` 导出、`import` 导入（和 Python 的 `from x import y` 一个思路）：

```javascript
// ── js/api.js：只管通信 ──────────────────────
const API = "http://127.0.0.1:8000";

export async function fetchTodos() {
    const res = await fetch(`${API}/todos`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function createTodo(title) { /* ... */ }
```

```javascript
// ── js/ui.js：只管渲染 ──────────────────────
export function renderTodos(todos, listEl) { /* createElement 那些活 */ }
export function showError(message) { /* ... */ }
```

```javascript
// ── js/main.js：入口，只做"接线" ─────────────
import { fetchTodos, createTodo } from "./api.js";
import { renderTodos, showError } from "./ui.js";

const listEl = document.querySelector("#todo-list");

async function refresh() {
    try {
        renderTodos(await fetchTodos(), listEl);
    } catch (err) {
        showError(err.message);
    }
}

document.querySelector("#add-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    await createTodo(/* ... */);
    await refresh();
});

refresh();
```

```html
<!-- 必须声明 type="module"，import 才能用 -->
<script src="js/main.js" type="module" defer></script>
```

拆分后的检验标准：**换后端地址只动 api.js，改界面只动 ui.js，加交互只动 main.js。**

> **注意**：`type="module"` 的页面**不能再双击用 file:// 打开**（浏览器安全限制），
> 需要本地服务器：在 frontend 目录跑 `python3 -m http.server 3000`，访问 `http://localhost:3000`。
> ——这就是"工程化"的第一个代价，也是为什么正式项目都要构建工具。

---

## 6. 代码整洁清单

- [ ] 魔法数字消灭：`margin-top: 37px` → 问自己为什么是 37？归到最近的间距令牌
- [ ] 选择器嵌套 ≤ 2 层：`.sidebar .nav .list .item a` 这种链条既慢又脆
- [ ] 每个函数只做一件事：函数名能用一个动词短语说清（`renderTodos` / `showError`）
- [ ] 删掉注释掉的死代码：Git 里都有，留着只会误导（02 章的价值再现）
- [ ] 用 **Prettier** 自动格式化：VSCode 装 Prettier 插件 → 设置里开启 "Format On Save"——
  从此缩进、引号、分号永远统一，**把风格问题交给机器，人只管逻辑**

---

## 7. 这套原则在 Vue 项目里长什么样

学完 17 章的你迟早会问：Vue 的 `.vue` 文件把模板、逻辑、样式写在**同一个文件**里——这不是违反了"CSS 单独成文件"吗？

**没有违反，是分离的粒度进化了**：原生项目"按技术分文件"（HTML/CSS/JS 各一堆），Vue"按**组件**分文件"——`TodoItem.vue` 里那点样式只属于这个组件，放一起反而是更彻底的"相关的放一起"。

对照表（`npm create vue@latest` 生成的标准结构）：

| 本章概念（原生） | Vue 项目里的对应 |
|---|---|
| `css/base.css`（令牌+全局） | `src/assets/main.css` —— **设计令牌依然全局定义**，这条不变！ |
| `css/components.css` | 各组件 `.vue` 文件里的 `<style scoped>`（scoped = 样式只作用于本组件，天然防污染） |
| `js/api.js` | `src/api/` 目录（同样"所有 fetch 集中一处"） |
| `js/ui.js` 的渲染函数 | 组件本身——模板就是声明式的"渲染函数" |
| `js/main.js` 入口 | `src/main.js` + `src/App.vue` |
| 页面级组织 | `src/views/`（页面）+ `src/components/`（可复用零件） |
| 跨组件共享的数据 | `src/stores/`（Pinia，17 章提过的名词） |

**结论**：本章的四个核心——令牌集中、语义命名、职责单一、结构跟着复杂度走——在 Vue 里一条都不作废，只是文件边界从"技术"变成了"组件"。

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `Cannot use import statement outside a module` | script 标签没加 `type="module"` | 加上 |
| import 报 CORS / 加载失败 | 用 file:// 双击打开了模块化页面 | `python3 -m http.server` 起本地服务器 |
| `import ... from "./api"` 找不到文件 | 浏览器里必须写全扩展名 | 写 `"./api.js"` |
| CSS 变量不生效 | 拼写错误不报错，静默失败 | F12 Styles 面板看变量值是否为空；变量名必须 `--` 开头 |
| 改了类名 JS 突然坏了 | 样式类被 JS 当选择器用 | JS 钩子用 `js-` 前缀类或 data- 属性，与样式类分离 |

---

## 小练习

1. 给 demo/frontend 的 `style.css` 做**令牌化改造**（自己练习用，可以先复制一份）：
   提取所有颜色和间距到 `:root` 变量，验收标准是组件规则里搜不到十六进制色值。
2. 把 demo/frontend 的 `app.js` 按第 5 节拆成 `api.js / ui.js / main.js` 三个模块，
   用 `python3 -m http.server` 跑起来，功能与原来完全一致。
3. 用 BEM 重命名你在 15 章练习里写的待办列表的所有类名。
4. 安装 Prettier 并开启保存自动格式化，把你已有的练习文件全部格式化一遍。

> 下一章：[19 · 设计美学：Apple 风格入门](19-apple-design.md) —— 工程优雅之后，视觉优雅。
