# 13 · HTML 基础

> 前端三件套第一课：HTML 负责**结构**（页面上有什么），CSS 负责**样式**（长什么样），JS 负责**行为**（点了会怎样）。
> 本章无任何前置知识要求，可与后端章节并行学习。预计学习时间：2~3 小时。

---

## 学习目标

1. 看懂并写出标准的 HTML 文档骨架
2. 掌握最常用的标签：标题、段落、列表、链接、图片
3. 理解**语义化**：为什么不全用 `<div>`
4. 会写表单（输入框、按钮、下拉框）——Web 交互的起点
5. 会用浏览器开发者工具查看任何网页的结构

---

## 1. HTML 是什么？

HTML（HyperText Markup Language）不是编程语言，是**标记语言**——用「标签」告诉浏览器"这是标题、这是段落、这是按钮"。

```html
<p>这是一个段落</p>
└┬┘            └─┬─┘
开始标签        结束标签（多了个 /）
```

- 大部分标签成对出现：`<p>...</p>`
- 少数标签自闭合：`<img>`、`<input>`、`<br>`
- 标签可以嵌套，但**必须像俄罗斯套娃一样规整**：`<p><b>对</b></p>` ✅，`<p><b>错</p></b>` ❌

---

## 2. 文档骨架：每个页面的起点

新建一个 `index.html`，敲下这段（VSCode 里输入 `!` 再按 Tab 可自动生成）：

```html
<!DOCTYPE html>                <!-- 声明这是 HTML5 文档，永远是第一行 -->
<html lang="zh-CN">            <!-- 根元素，lang 帮助搜索引擎和读屏软件 -->
<head>
    <!-- head 放"关于页面的信息"，用户看不见 -->
    <meta charset="UTF-8">     <!-- 字符编码，没有它中文会乱码 -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                               <!-- 移动端适配必备，没有它手机上字会特别小 -->
    <title>我的第一个页面</title>  <!-- 浏览器标签页上显示的标题 -->
</head>
<body>
    <!-- body 放页面上实际显示的内容 -->
    <h1>Hello, HTML!</h1>
</body>
</html>
```

双击这个文件用浏览器打开就能看到效果——HTML 学习**零环境配置**。

---

## 3. 最常用的标签

```html
<!-- 标题：h1 ~ h6，一个页面只用一个 h1 -->
<h1>一级标题</h1>
<h2>二级标题</h2>

<!-- 段落与强调 -->
<p>这是段落。<strong>加粗强调</strong>，<em>斜体强调</em>。</p>

<!-- 列表：ul 无序（圆点），ol 有序（编号），li 是列表项 -->
<ul>
    <li>学 HTML</li>
    <li>学 CSS</li>
</ul>
<ol>
    <li>第一步</li>
    <li>第二步</li>
</ol>

<!-- 链接：href 是目的地；target="_blank" 新标签页打开 -->
<a href="https://developer.mozilla.org" target="_blank">MDN 文档</a>

<!-- 图片：src 是图片地址，alt 是加载失败/读屏时的文字描述 -->
<img src="cat.png" alt="一只橘猫">

<!-- 分组容器：div 块级（独占一行），span 行内（嵌在文字里） -->
<div>我是一个块</div>
<p>这句话里<span>这几个字</span>被 span 包住了</p>

<!-- 注释 -->
<!-- 用户看不到我，但查看源码能看到——别写密码！ -->
```

### 全局属性：id 与 class

```html
<p id="intro">id 全页面唯一，一个元素一个</p>
<p class="highlight big">class 可以重复用，一个元素可以有多个（空格分隔）</p>
```

这两个属性本章还用不上，但它们是 CSS 选样式（14 章）和 JS 找元素（15 章）的**门牌号**——先混个脸熟。

---

## 4. 语义化：别全用 div

下面两种写法显示效果可以做到一样，但右边是专业写法：

```html
<!-- ❌ div 汤：机器完全不知道每块是什么 -->
<div>网站标题</div>
<div>菜单</div>
<div>正文...</div>
<div>版权信息</div>

<!-- ✅ 语义化：结构自带含义 -->
<header>网站标题</header>
<nav>菜单</nav>
<main>
    <article>
        <h2>文章标题</h2>
        <p>正文...</p>
    </article>
</main>
<footer>版权信息</footer>
```

语义化的价值：搜索引擎更懂你的页面（SEO）、读屏软件能正确朗读（无障碍）、半年后的你能看懂自己的代码。

> **要点**：记住这组常用语义标签即可：`header` / `nav` / `main` / `section` / `article` / `footer`。
> 实在没有合适语义的"纯分组"再用 `div`。

---

## 5. 表单：Web 交互的起点

表单是用户向后端提交数据的入口——正是你在 FastAPI 章节里接收的那些请求体的来源。

```html
<form id="signup">
    <!-- label 的 for 对应 input 的 id：点击文字也能聚焦输入框 -->
    <label for="username">用户名</label>
    <input type="text" id="username" name="username" placeholder="请输入用户名" required>

    <label for="pwd">密码</label>
    <input type="password" id="pwd" name="pwd">

    <label for="email">邮箱</label>
    <input type="email" id="email" name="email">   <!-- 自带格式校验 -->

    <label for="level">水平</label>
    <select id="level" name="level">               <!-- 下拉框 -->
        <option value="beginner">新手</option>
        <option value="pro">高手</option>
    </select>

    <label>
        <input type="checkbox" name="agree"> 同意用户协议
    </label>

    <label for="bio">简介</label>
    <textarea id="bio" name="bio" rows="4"></textarea>   <!-- 多行文本 -->

    <button type="submit">注册</button>
</form>
```

`input` 的常用 `type`：`text` / `password` / `email` / `number` / `date` / `checkbox` / `radio` / `file`。
换个 type，浏览器自动换键盘（手机上）、自动做基础校验——**能用原生就别自己造**。

> **要点**：`required`、`type="email"` 这类**浏览器内置校验**只是第一道体验层防线，
> 用户可以绕过——所以后端的 Pydantic 校验（06 章）永远不能省。前后端校验是"都要做"，不是二选一。

---

## 6. 实例解读：你的 Audio Book 前端

回头看你项目里的 [Frontend/main.html](https://github.com/Syonling/AI_Full_Stack_Learning_Handbook)（本地文件），现在你应该能完整看懂它的结构了：

```html
<form id="textinput">                          <!-- 一个表单 -->
    <textarea name="input" id="inputText"></textarea>   <!-- 多行输入框 -->
    <button type="button" id="submitButton">Submit</button>
</form>
<button type="button" id="inquiryButton">Inquiry</button>
<div id="outputText"></div>                    <!-- 空容器，等 JS 往里填内容 -->
```

注意细节：按钮写了 `type="button"`——因为按钮在 `<form>` 里默认是 `type="submit"`，
点击会触发表单默认提交（刷新页面）；这里改用 JS 自己处理（15/16 章的内容），所以显式声明为普通按钮。

---

## 7. 开发者工具：前端学习的显微镜

在任何网页上按 **`F12`**（或 macOS `Cmd + Option + I`，或右键 → 检查）：

- **Elements（元素）面板**：查看页面真实的 HTML 结构，点击任意元素高亮对应区域
- 左上角的**箭头图标**（`Cmd + Shift + C`）：点页面上任何东西，直接跳到它的代码
- 双击元素文字可以**临时修改**页面内容（刷新还原）——用它拆解你喜欢的任何网站

> **要点**：从今天起养成习惯——看到好看的网页就按 F12 看看人家怎么写的。这是前端最好的免费教材。

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 中文显示乱码 | 缺 `<meta charset="UTF-8">` | 加在 head 第一行 |
| 手机上文字特别小 | 缺 viewport meta | 加 `<meta name="viewport" ...>` |
| 图片显示裂图 | src 路径错误 | 检查相对路径（相对的是 HTML 文件的位置） |
| 点按钮页面莫名刷新 | form 里的按钮默认是 submit | 加 `type="button"`，或在 JS 里阻止默认行为（16 章） |
| 标签显示成了文字 | 标签没闭合或尖括号写错 | 用 VSCode 的高亮检查配对 |
| 改了文件浏览器没变化 | 没保存 / 没刷新 | `Cmd + S` 保存，浏览器 `Cmd + R` 刷新 |

---

## 小练习

1. 手写（不用生成器）一个完整骨架的 `about.html`：包含你的名字（h1）、三行自我介绍（p）、
   一个"我在学的技术"无序列表、一张图片、一个指向你 GitHub 仓库的链接。
2. 给它加一个"联系我"表单：姓名（text）、邮箱（email）、留言（textarea）、提交按钮。
3. 用语义化标签（header/main/footer）重新组织第 1 题的页面。
4. 打开你的文档网站，按 F12 用箭头工具点侧边栏、导航栏，观察 VitePress 用了哪些标签和 class。

> 下一章：[14 · CSS 基础](14-css-basics.md) —— 让这些"素面朝天"的页面好看起来。
