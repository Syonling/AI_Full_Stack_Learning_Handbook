# 14 · CSS 基础

> CSS 负责**样式**：颜色、大小、间距、布局。本章重点是**盒模型**和 **Flex 布局**——它们是所有页面布局的基础。
> 预计学习时间：3~4 小时。需要第 13 章的 HTML 知识。

---

## 学习目标

1. 掌握三种引入 CSS 的方式，知道该用哪种
2. 会用选择器精确命中想要的元素
3. 理解**盒模型**（margin / border / padding）——CSS 的第一性原理
4. 熟练使用 **Flex 布局**（居中、排列、分配空间）
5. 会写基础的响应式（手机/电脑不同样式）
6. 会用开发者工具调试样式

---

## 1. 三种引入方式

```html
<!-- 方式 1：外部文件（✅ 正式项目标准做法：结构与样式分离，可缓存复用）-->
<head>
    <link rel="stylesheet" href="style.css">
</head>

<!-- 方式 2：<style> 标签（适合单文件小页面，你的 main.html 就是这种）-->
<head>
    <style>
        p { color: gray; }
    </style>
</head>

<!-- 方式 3：行内样式（❌ 尽量避免：无法复用、优先级混乱）-->
<p style="color: red;">只影响这一个元素</p>
```

CSS 规则的语法：

```css
选择器 {
    属性: 值;         /* 每条声明以分号结尾 */
    color: #333;      /* 文字颜色 */
    font-size: 16px;  /* 字号 */
}
```

---

## 2. 选择器：命中你要的元素

```css
/* 元素选择器：所有 <p> */
p { color: gray; }

/* 类选择器（最常用）：所有 class="highlight" 的元素 */
.highlight { background: yellow; }

/* id 选择器：id="header" 的那一个元素 */
#header { font-size: 24px; }

/* 后代选择器：nav 里面的所有 a */
nav a { text-decoration: none; }

/* 多个选择器共用一套样式 */
h1, h2, h3 { font-family: Georgia, serif; }

/* 伪类：特定状态 */
button:hover { background: #2563eb; }   /* 鼠标悬停时 */
input:focus { border-color: blue; }     /* 输入框聚焦时 */
li:first-child { font-weight: bold; }   /* 第一个 li */
```

> **要点**：日常 90% 的场景用**类选择器**。id 留给 JS 定位用，元素选择器留给全局基调
>（如给 body 设字体）。多个规则命中同一元素时，更"具体"的赢（id > class > 元素），
> 同级则写在后面的赢——被覆盖时用 F12 一看便知。

---

## 3. 盒模型：CSS 的第一性原理

**页面上每个元素都是一个矩形盒子**，从内到外四层：

```
┌─────────────────── margin（外边距：和别人的距离）
│  ┌──────────────── border（边框）
│  │  ┌───────────── padding（内边距：内容和边框的距离）
│  │  │   content    （内容：文字/图片）
│  │  └─────────────
│  └────────────────
└───────────────────
```

```css
.card {
    width: 300px;
    padding: 16px;              /* 四边各 16px */
    padding: 8px 16px;          /* 上下 8px，左右 16px（两值语法）*/
    border: 1px solid #ddd;     /* 粗细 样式 颜色 */
    border-radius: 8px;         /* 圆角 */
    margin: 24px auto;          /* 上下 24px；左右 auto = 块级元素水平居中 */
}
```

**必须知道的坑与解药**：默认情况下 `width` 只算 content，padding 和 border 会把盒子越撑越大。
解药是全局改用更符合直觉的计算方式——**几乎所有项目的第一行 CSS**：

```css
* {
    box-sizing: border-box;    /* width = content + padding + border，所见即所得 */
    margin: 0;                 /* 顺手清掉浏览器默认边距 */
    padding: 0;
}
```

### 常用单位

| 单位 | 含义 | 用途 |
|---|---|---|
| `px` | 像素，绝对单位 | 边框、小间距 |
| `rem` | 相对根字号（默认 1rem = 16px） | 字号、间距（用户调大字体时能跟着缩放）|
| `%` | 相对父元素 | 宽度 |
| `vw` / `vh` | 视口宽/高的 1% | 全屏区块（`height: 100vh`）|

---

## 4. Flex 布局：现代布局的 80%

在 Flex 出现之前，"让两个东西并排"、"垂直居中"都是老大难。现在只需：
**给父元素加 `display: flex`，子元素自动变成可灵活排列的项目**。

```css
.container {
    display: flex;
    flex-direction: row;        /* 主轴方向：row 水平（默认）| column 垂直 */
    justify-content: space-between;  /* 主轴上如何分配 */
    align-items: center;        /* 交叉轴上如何对齐 */
    gap: 12px;                  /* 项目之间的间距（超好用，代替 margin hack）*/
}
```

`justify-content`（主轴分配）的常用值，假设三个盒子水平排列：

```
flex-start     |■ ■ ■        |     靠头
center         |   ■ ■ ■     |     居中
flex-end       |        ■ ■ ■|     靠尾
space-between  |■     ■     ■|     两端顶格，中间均分
space-around   | ■    ■    ■ |     每个项目两侧等距
```

### 两个背下来的"配方"

```css
/* 配方 1：完美居中（水平+垂直）—— 面试都会问 */
.center {
    display: flex;
    justify-content: center;
    align-items: center;
}

/* 配方 2：左右布局（左边固定，右边撑满）*/
.row {
    display: flex;
    gap: 8px;
}
.row .grow { flex: 1; }    /* 这个子元素占掉所有剩余空间 */
```

配方 2 正是 Todo 列表每一行的做法：`[✓] 任务标题-----------[删除]`——
复选框和删除按钮各占自身大小，标题 `flex: 1` 撑满中间。

### Grid 一瞥（知道有它即可）

Flex 是一维（一行或一列），Grid 是二维（行列同时控制）。等宽卡片网格用 Grid 最简单：

```css
.cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);   /* 三等分 */
    gap: 16px;
}
```

新手阶段：**一维用 Flex，规整网格用 Grid**，够用两年。

---

## 5. 文字、颜色与手感

```css
body {
    font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
                                /* 字体栈：从左往右找，都没有就用默认无衬线 */
    font-size: 16px;
    line-height: 1.6;           /* 行高 1.5~1.7 阅读最舒适 */
    color: #333;                /* 正文别用纯黑 #000，#333 更柔和 */
    background: #f6f7f9;
}

.btn {
    background: #2563eb;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    cursor: pointer;            /* 鼠标变小手：可点击的暗示 */
    transition: background 0.2s;   /* 颜色变化带 0.2 秒过渡，立刻显得"高级" */
}
.btn:hover { background: #1d4ed8; }
```

颜色写法：`#2563eb`（十六进制，最常用）、`rgb(37 99 235)`、
`rgba(0 0 0 / 0.5)`（带透明度）。配色新手建议：直接抄 [Tailwind 调色板](https://tailwindcss.com/docs/customizing-colors) 的现成色阶。

---

## 6. 响应式：一套代码适配手机和电脑

核心工具是**媒体查询**——满足条件时才生效的 CSS：

```css
/* 默认样式（手机优先写法）*/
.cards { display: grid; grid-template-columns: 1fr; gap: 16px; }

/* 屏幕宽度 ≥ 768px 时（平板/电脑）：三列 */
@media (min-width: 768px) {
    .cards { grid-template-columns: repeat(3, 1fr); }
}

/* 跟随系统深色模式（你的 handbook.html 就是这么做的）*/
@media (prefers-color-scheme: dark) {
    body { background: #12151a; color: #e8ebef; }
}
```

配合第 13 章的 viewport meta 标签，这就是响应式的全部基础。
开发者工具左上角的**手机图标**（`Cmd + Shift + M`）可以模拟各种手机屏幕来调试。

---

## 7. 用 F12 调试样式

Elements 面板选中元素后，右侧 **Styles** 区域：

- 能看到该元素命中的**所有规则**，被覆盖的会显示删除线（一眼看出"为什么我的样式没生效"）
- 每条属性前有复选框，可以**临时开关**；点击值可以**直接改数字**（方向键微调）
- 底部的盒模型图实时显示 margin/border/padding 的具体数值

> **要点**：调样式的正确姿势是**先在 F12 里改到满意，再把值抄回代码**——比"改代码→保存→刷新"的循环快十倍。

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 样式完全没生效 | link 路径错 / 选择器拼错 | F12 Network 看 css 是否 404；Elements 看规则是否命中 |
| 类选择器不生效 | CSS 里忘了写点：`highlight {}` | 类选择器必须 `.highlight {}` |
| 宽度总是比设置的大 | 默认盒模型把 padding 加到 width 外 | 全局 `box-sizing: border-box` |
| margin: auto 不居中 | 元素不是块级 / 没有设置 width | 确认 `display: block` 且有明确宽度；或直接用 Flex 居中 |
| hover 在手机上"卡住" | 手机没有悬停概念 | 正常现象；关键交互别只依赖 hover |
| 两个元素之间的间距比预期大 | 上下 margin 合并（外边距折叠） | 改用 padding 或 Flex 的 gap 控制间距 |

---

## 小练习

1. 给 13 章的 `about.html` 建一个外部 `style.css`：全局 `box-sizing`、正文字体与行高、页面内容宽度限制在 720px 并水平居中。
2. 把"我在学的技术"列表改造成卡片：白底、圆角、阴影（`box-shadow: 0 1px 3px rgba(0 0 0 / 0.1)`）、hover 时背景微变。
3. 用 Flex 实现一个顶部导航栏：左边站点名，右边三个链接，垂直居中，两端对齐。
4. 加一个媒体查询：屏幕小于 600px 时，第 3 题的导航改为垂直堆叠（`flex-direction: column`）。
5. 打开你的 [Frontend/main.html](../demo/)，用本章知识美化它：按钮 hover 效果、输出区圆角卡片化——全部先在 F12 里调好再抄回代码。

> 下一章：[15 · JavaScript 基础](15-javascript-basics.md) —— 让页面动起来。
