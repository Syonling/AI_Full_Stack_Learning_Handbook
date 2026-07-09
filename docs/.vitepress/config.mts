import { defineConfig } from 'vitepress'

// GitHub Pages 项目站点部署在 /<仓库名>/ 路径下。
// deploy.yml 会自动注入 DOCS_BASE=/<仓库名>/；本地开发默认 '/'，无需任何修改。
const base = process.env.DOCS_BASE || '/'

export default defineConfig({
  lang: 'zh-CN',
  title: 'AI 全栈学习手册',
  description:
    'FastAPI · SQLite · Python 后端 · AI Agent —— 0 基础全栈学习系统（教程 + 速查 + 实践）',
  base,

  // docs/ 正文保留了指向站点之外的相对链接（如 ../demo/），按约定不修改正文
  ignoreDeadLinks: true,

  head: [['link', { rel: 'icon', type: 'image/svg+xml', href: `${base}logo.svg` }]],

  // 代码高亮：VitePress 内置 Shiki，原生支持 python / js / html / bash / json 等
  markdown: {
    lineNumbers: false,
    // ```gitignore 代码块不在 Shiki 内置语言里，按 ini 语法高亮（注释/键值格式一致）
    languageAlias: { gitignore: 'ini' },
  },

  themeConfig: {
    // ── 顶部导航 ─────────────────────────────
    nav: [
      { text: '首页', link: '/' },
      { text: '教程', link: '/01-python-backend-basics', activeMatch: '^/\\d' },
      // Code Search：docs/public/handbook.html（构建时从根 handbook.html 复制）
      // 以 / 开头的链接主题会自动补 base 前缀；target: '_blank' 让浏览器直接打开而不走 SPA 路由
      { text: 'Code Search', link: '/handbook.html', target: '_blank' },
    ],

    // ── 左侧目录（顺序 = 文件编号 = 学习顺序）──
    sidebar: [
      {
        text: '基础工具',
        collapsed: false,
        items: [
          { text: '01 · Python 后端基础', link: '/01-python-backend-basics' },
          { text: '02 · Git 版本控制', link: '/02-git-basics' },
          { text: '03 · 日志与调试', link: '/03-logging-and-debugging' },
        ],
      },
      {
        text: '后端主线',
        collapsed: false,
        items: [
          { text: '04 · FastAPI 入门', link: '/04-fastapi-basics' },
          { text: '05 · SQLite 基础', link: '/05-sqlite-basics' },
          { text: '06 · FastAPI 进阶', link: '/06-fastapi-advanced' },
          { text: '07 · 整合实战：CRUD API', link: '/07-fastapi-sqlite-crud' },
        ],
      },
      {
        text: '工程化落地',
        collapsed: false,
        items: [
          { text: '08 · 配置与环境变量', link: '/08-config-and-env' },
          { text: '09 · FastAPI 工程化', link: '/09-fastapi-engineering' },
          { text: '10 · 测试与项目结构', link: '/10-testing-and-structure' },
          { text: '11 · 部署入门', link: '/11-deployment' },
        ],
      },
      {
        text: '进阶选修',
        collapsed: false,
        items: [{ text: '12 · AI Agent 开发', link: '/12-ai-agents' }],
      },
    ],

    // ── 上一章 / 下一章（按 sidebar 顺序自动生成）──
    docFooter: { prev: '上一章', next: '下一章' },

    // ── 右侧本页目录（TOC）──
    outline: { level: [2, 3], label: '本页目录' },

    // ── 本地全文搜索（零依赖，支持中文）──
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索', buttonAriaLabel: '搜索文档' },
          modal: {
            noResultsText: '没有找到结果',
            resetButtonTitle: '清空关键词',
            footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' },
          },
        },
      },
    },

    // ── 界面文案汉化 ──
    darkModeSwitchLabel: '深色模式',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    sidebarMenuLabel: '目录',
    returnToTopLabel: '回到顶部',
    langMenuLabel: '语言',
    externalLinkIcon: true,

    footer: {
      message: 'AI 全栈学习手册 · 用 VitePress 构建',
    },

    // 上传 GitHub 后，把下面的链接换成你的仓库地址即可在导航栏显示 GitHub 图标
    socialLinks: [{ icon: 'github', link: 'https://github.com/Syonling/AI_Full_Stack_Learning_Handbook' }],
  },
})
