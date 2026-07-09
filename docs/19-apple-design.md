# 19 · 设计美学：Apple 风格入门

> 目标不是"抄苹果"，而是学会苹果设计背后**可迁移的纪律**：克制、留白、层次。
> 本章基于 Apple 官方的 [Human Interface Guidelines（HIG）](https://developer.apple.com/design/human-interface-guidelines)
> 和 Apple.com 本身（最好的活教材），把原则翻译成可直接落地的 CSS。
> 预计学习时间：3~4 小时。强依赖 14 章（CSS）和 18 章（设计令牌）。

---

## 学习目标

1. 理解 HIG 三原则：清晰（Clarity）、内容优先（Deference）、层次（Depth）
2. 掌握 Apple 观感的五个支柱：留白、字阶、克制的色彩、大圆角、毛玻璃
3. 得到一套可复用的「Apple 风设计令牌」
4. 亲手把一个普通页面改造成 Apple 风格
5. 知道如何持续自学：读 HIG、拆解 Apple.com

---

## 1. HIG 三原则：所有细节的总纲

打开 apple.com 任意产品页，你感受到的"高级"来自三条原则：

| 原则 | 含义 | 在网页上的体现 |
|---|---|---|
| **Clarity 清晰** | 任何时候用户都不需要猜 | 文字大而易读、图标含义精确、对比度足够、一眼知道什么可以点 |
| **Deference 内容优先** | 界面是仆人，内容是主人 | 界面元素退后（浅底、细线、轻阴影），产品图和标题占据舞台中心 |
| **Depth 层次** | 用视觉层级引导注意力 | 重要的大、次要的灰、模糊的远——不靠加粗加红，靠"层"来分主次 |

**反面教材自查**：如果你的页面同时有 3 种以上强调色、5 种字号、到处加粗——那是在"喊"，
不是在"说"。Apple 风格的本质是**做减法**。

---

## 2. 留白：8pt 间距系统

Apple 界面的"呼吸感"来源不是某个特效，是**慷慨且成体系的留白**：

- 所有间距是 **8 的倍数**（8 / 16 / 24 / 32 / 48 / 64…），小微调允许 4
- 关系近的元素间距小，关系远的间距大——**用距离表达分组**，代替画框线
- 当你犹豫"这里空隙要不要再大点"时，答案几乎总是：**要**

```css
:root {
    --space-1: 8px;    --space-2: 16px;
    --space-3: 24px;   --space-4: 32px;
    --space-6: 48px;   --space-8: 64px;
}
.section { padding-block: var(--space-8); }     /* 大区块之间：非常大方 */
.card { padding: var(--space-3); }
.card__title { margin-bottom: var(--space-1); } /* 标题和正文：紧凑成组 */
```

---

## 3. 字体排印：对比即层次

Apple 的字体系统 SF Pro 不能直接商用，但 `-apple-system` 字体栈在 Mac/iPhone 上**就是它**：

```css
:root {
    --font-body: -apple-system, BlinkMacSystemFont, "PingFang SC",
                 "Helvetica Neue", "Microsoft YaHei", sans-serif;
}
```

Apple 排印的三个手法：

1. **字号拉开悬殊对比**——标题不是比正文大一点，是大很多：

   ```css
   .hero__title { font-size: 48px; font-weight: 700; letter-spacing: -0.02em; }
   .hero__subtitle { font-size: 21px; font-weight: 400; color: var(--color-text-muted); }
   body { font-size: 17px; }      /* Apple 正文惯用 17px，比默认 16 稍大更从容 */
   ```

2. **大标题微收字距**（`letter-spacing: -0.02em`）——大字号下更紧凑精致，这是 Apple 标题的隐藏配方
3. **用灰度分级，不用字号轰炸**：次要信息不缩小字号，而是降为 `--color-text-muted`——层次感来自颜色深浅

---

## 4. 色彩纪律：中性打底 + 一个强调色

Apple 页面 95% 的面积是黑、白、灰，彩色只出现在**要你点的地方**：

```css
:root {
    /* 中性色打底 */
    --color-bg: #f5f5f7;           /* Apple 官网标志性的暖灰背景 */
    --color-surface: #ffffff;
    --color-text: #1d1d1f;         /* Apple 的"黑"：不是纯黑 */
    --color-text-muted: #6e6e73;   /* Apple 的"灰" */

    /* 唯一强调色：Apple 系统蓝 */
    --color-accent: #0071e3;       /* 官网按钮蓝；系统 UI 蓝是 #007AFF */
}
```

Apple 官方系统色（HIG 公布的调色板，需要多色时从这里取）：

| 用途 | Light | 示例场景 |
|---|---|---|
| Blue（默认强调）| `#007AFF` | 链接、主按钮 |
| Green | `#34C759` | 成功、完成 |
| Red | `#FF3B30` | 删除、错误 |
| Orange | `#FF9500` | 警告 |

深色模式同样一套令牌覆盖（18 章的方法直接复用）：

```css
@media (prefers-color-scheme: dark) {
    :root {
        --color-bg: #000000;        /* Apple 深色模式用纯黑打底 */
        --color-surface: #1c1c1e;
        --color-text: #f5f5f7;
        --color-text-muted: #86868b;
        --color-accent: #0a84ff;    /* 深色下的蓝更亮一档 */
    }
}
```

---

## 5. Apple signature 三件套

### ① 大圆角

```css
.card { border-radius: 18px; }      /* Apple 卡片惯用 14~20px，明显大于"默认 8px" */
.btn { border-radius: 980px; }      /* 官网按钮：胶囊形（半径给到夸张即可）*/
```

### ② 毛玻璃（frosted glass）——最具辨识度的一招

macOS 菜单栏、iOS 控制中心、Apple.com 导航栏都是它：

```css
.navbar {
    position: sticky; top: 0;
    background: rgb(255 255 255 / 0.72);   /* 半透明底 */
    backdrop-filter: saturate(180%) blur(20px);   /* ★ 模糊透出下层内容 */
    -webkit-backdrop-filter: saturate(180%) blur(20px);  /* Safari 前缀 */
}
```

`saturate(180%)` 是点睛之笔——透出的色彩更鲜润，这是 Apple 官网导航栏的实际配方。

### ③ 极轻的阴影与描边

Apple 几乎不用重阴影，卡片的"浮起感"来自**细描边 + 若有若无的阴影**：

```css
.card {
    border: 1px solid rgb(0 0 0 / 0.06);
    box-shadow: 0 2px 12px rgb(0 0 0 / 0.06);   /* 透明度个位数！ */
}
```

> **要点**：见到 `box-shadow: 0 4px 20px rgba(0,0,0,0.4)` 这种浓黑投影，基本可以断定不是 Apple 风。

---

## 6. 动效：感觉不到才是好动效

```css
:root { --transition: 0.25s cubic-bezier(0.25, 0.1, 0.25, 1); }

.btn { transition: transform var(--transition), background var(--transition); }
.btn:hover { transform: scale(1.02); }     /* 微妙放大，不是跳起来 */
.btn:active { transform: scale(0.97); }    /* 按下微缩——"按得动"的手感 */

/* 无障碍纪律：用户系统里关掉了动效，就全部尊重 */
@media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
}
```

规则：时长 0.2~0.35s、只动 `transform` 和 `opacity`（性能好）、幅度小到"感觉顺滑但说不出哪里动了"。

---

## 7. 动手实战：给你的 Todo 页面换上 Apple 风

把下面这套完整主题保存为 `style-apple.css`，在你自己练习用的 Todo 页面里替换原来的样式引入（demo 原文件不动，复制一份来玩）：

```css
/* ===== Apple 风主题（基于本章全部令牌）===== */
* { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --font-body: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
    --color-bg: #f5f5f7;
    --color-surface: #ffffff;
    --color-text: #1d1d1f;
    --color-text-muted: #6e6e73;
    --color-accent: #0071e3;
    --color-danger: #ff3b30;
    --space-1: 8px; --space-2: 16px; --space-3: 24px; --space-6: 48px;
    --transition: 0.25s cubic-bezier(0.25, 0.1, 0.25, 1);
}

body {
    font-family: var(--font-body);
    font-size: 17px;
    line-height: 1.5;
    color: var(--color-text);
    background: var(--color-bg);
}

.container { max-width: 560px; margin: 0 auto; padding: var(--space-6) var(--space-2); }

h1 { font-size: 40px; font-weight: 700; letter-spacing: -0.02em; }
.subtitle { color: var(--color-text-muted); margin: var(--space-1) 0 var(--space-3); }

.add-form { display: flex; gap: var(--space-1); margin-bottom: var(--space-3); }
.add-form input {
    flex: 1;
    font-size: 17px;
    padding: 12px var(--space-2);
    border: 1px solid rgb(0 0 0 / 0.1);
    border-radius: 12px;
    background: var(--color-surface);
    outline: none;
    transition: border-color var(--transition), box-shadow var(--transition);
}
.add-form input:focus {
    border-color: var(--color-accent);
    box-shadow: 0 0 0 4px rgb(0 113 227 / 0.15);   /* Apple 式聚焦光环 */
}

button {
    font-size: 15px; font-weight: 500;
    padding: 12px 22px;
    border: none; border-radius: 980px;            /* 胶囊按钮 */
    background: var(--color-accent); color: #fff;
    cursor: pointer;
    transition: transform var(--transition), opacity var(--transition);
}
button:hover { opacity: 0.9; transform: scale(1.02); }
button:active { transform: scale(0.97); }

ul { list-style: none; }
.todo-row {
    display: flex; align-items: center; gap: var(--space-2);
    background: var(--color-surface);
    border: 1px solid rgb(0 0 0 / 0.06);
    border-radius: 18px;
    padding: var(--space-2) var(--space-3);
    margin-bottom: var(--space-1);
    box-shadow: 0 2px 12px rgb(0 0 0 / 0.04);
    transition: transform var(--transition), box-shadow var(--transition);
}
.todo-row:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgb(0 0 0 / 0.08); }
.todo-row .title { flex: 1; }
.todo-row .title.done { color: var(--color-text-muted); text-decoration: line-through; }
.todo-row button { background: transparent; color: var(--color-danger); padding: 6px 10px; }

footer p { color: var(--color-text-muted); font-size: 14px; margin-top: var(--space-2); text-align: center; }

.error-banner {
    background: rgb(255 59 48 / 0.08);
    border: 1px solid rgb(255 59 48 / 0.25);
    color: var(--color-danger);
    border-radius: 12px;
    padding: 12px var(--space-2);
    margin-bottom: var(--space-2);
}
.hidden { display: none; }

@media (prefers-color-scheme: dark) {
    :root {
        --color-bg: #000; --color-surface: #1c1c1e;
        --color-text: #f5f5f7; --color-text-muted: #86868b;
        --color-accent: #0a84ff;
    }
    .todo-row, .add-form input { border-color: rgb(255 255 255 / 0.1); }
}

@media (prefers-reduced-motion: reduce) {
    * { transition: none !important; }
}
```

**换肤后逐条对照体会**：暖灰背景 `#f5f5f7`、17px 正文、胶囊按钮、18px 圆角卡片、
个位数透明度的阴影、聚焦光环、hover 时卡片轻浮 1px——每一条都能在本章前六节找到出处。
再把系统切到深色模式看一眼：**因为全部走令牌，深色版自动成立**（18 章的投资在此兑现）。

---

## 8. 持续自学的三个渠道

1. **读 HIG**：<https://developer.apple.com/design/human-interface-guidelines>
   ——推荐从 Foundations 下的 *Layout*、*Typography*、*Color* 三篇读起（讲原则，不讲 iOS 专属控件的部分全部可迁移）
2. **拆 Apple.com**：F12 打开 Elements（13 章的技能），量它的间距是不是 8 的倍数、
   看导航栏的 backdrop-filter 参数、看按钮的 border-radius——**验证本章说的每一条**
3. **WWDC 设计讲座**：Apple 开发者官网搜 "Design" 分类，
   《Essential Design Principles》是入门首选（有字幕）

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 毛玻璃没效果 | 元素背景是全不透明色 | 背景必须半透明（`rgb(255 255 255 / 0.72)`），blur 才有东西可透 |
| Safari 里毛玻璃失效 | 缺前缀 | 补 `-webkit-backdrop-filter` |
| 页面"高级感"出不来 | 强调色用了三四种 / 间距随手写 | 回到纪律：一个 accent、8 的倍数 |
| 深色模式下惨不忍睹 | 颜色写死没走令牌 | 回 18 章补令牌化 |
| 大标题发散不精致 | 忘了负字距 | 大标题加 `letter-spacing: -0.02em` |
| 动效卡顿 | transition 了 width/height/margin | 只动 transform 和 opacity |

---

## 小练习

1. 完成第 7 节的 Todo 换肤，深浅两个模式各截一张图，和原版对比。
2. 打开 apple.com，用 F12 找出：导航栏的 backdrop-filter 具体参数、主按钮的 border-radius、
   任意产品页 hero 区的上下 padding——验证是否符合本章描述。
3. 只改 `--color-accent` 一个变量，把你的 Apple 风主题分别调成 Green（#34C759）和 Orange（#FF9500）版本，
   体会"设计令牌 + 色彩纪律"的威力。
4. 给你 13/14 章练习做的 about.html 页面做一次完整的 Apple 风改造。

> 后端同学别走：[20 · 后端代码组织](20-backend-engineering.md) —— 同样的工程优雅，Python 版。
