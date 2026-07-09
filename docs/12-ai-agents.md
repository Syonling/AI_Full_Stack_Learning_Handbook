# 12 · AI Agent 开发：Agent / MCP / Skill / LangChain / LangGraph

> 本章目标：建立 AI Agent 开发的完整概念地图，看懂并能写出基础的 Agent 代码。
> 本章为**纯教学章节**（不含配套 demo 项目），代码示例可自行创建文件练习。
> 预计学习时间：4~6 小时。建议先学完 01（Python 基础）和 04（FastAPI 入门）。

---

## 学习目标

1. 理解什么是 **Agent**，它和普通"调用一次大模型"有什么区别
2. 掌握 **Tool Use（工具调用）**——Agent 的核心机制
3. 理解 **MCP**（Model Context Protocol）解决什么问题
4. 理解 **Skill**（技能）是什么、怎么组织
5. 会用 **LangChain** 做基础的 LLM 应用编排
6. 会用 **LangGraph** 构建有状态的 Agent 工作流
7. 知道**什么场景选什么工具**（直接 API / LangChain / LangGraph）

---

## 1. 从"一次调用"到 Agent

### 1.1 最普通的 LLM 调用

先看最简单的形态——发一个问题，拿一个回答（以 Anthropic 官方 SDK 为例）：

```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."   # 你的 API key
```

```python
import anthropic

client = anthropic.Anthropic()   # 自动读取环境变量里的 API key

response = client.messages.create(
    model="claude-opus-4-8",     # 模型 ID
    max_tokens=16000,            # 输出长度上限
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ],
)

for block in response.content:
    if block.type == "text":
        print(block.text)        # Paris
```

这叫**单次调用（single LLM call）**：一问一答，模型只能依靠训练时学到的知识，
不能查数据库、不能上网、不能执行代码。

### 1.2 什么是 Agent？

**Agent = LLM + 工具（Tools）+ 循环（Loop）**

- **LLM** 负责"思考"：理解任务、决定下一步做什么
- **工具** 负责"动手"：查数据库、调 API、读写文件、执行代码
- **循环** 把两者串起来：模型决定调用工具 → 程序执行工具 → 把结果喂回模型 → 模型继续决定……直到任务完成

```
用户: "帮我查一下巴黎明天的天气，然后写一封提醒带伞的邮件"

┌─────────────────── Agent 循环 ───────────────────┐
│  LLM 思考: 我需要先查天气 → 调用 get_weather 工具   │
│  程序执行: get_weather("Paris") → "明天有雨, 15°C"  │
│  LLM 思考: 有雨，需要写邮件 → 调用 send_email 工具   │
│  程序执行: send_email(...) → "发送成功"             │
│  LLM 思考: 任务完成 → 输出总结                      │
└──────────────────────────────────────────────────┘
```

> **要点**：判断一个系统是不是 Agent，看**"下一步做什么"是谁决定的**。
> 流程写死在代码里 → 这是**工作流（workflow）**；
> 由模型根据情况自主决定 → 这是 **Agent**。

### 1.3 什么时候需要 Agent？

不是所有任务都需要 Agent。经验法则（从简单到复杂选择）：

| 任务类型 | 用什么 | 例子 |
|---|---|---|
| 单次问答/分类/摘要/提取 | 单次 API 调用 | "把这段话翻译成英文" |
| 步骤固定的多步流程 | 工作流（代码控制顺序）| "先摘要 → 再翻译 → 再存库" |
| 步骤无法预先确定的开放任务 | Agent | "调研这个 bug 的原因并修复它" |

---

## 2. Tool Use（工具调用）——Agent 的核心机制

### 2.about1 原理

LLM 本身**不能**执行任何代码。所谓"工具调用"实际是一个约定：

1. 你在请求里**声明**有哪些工具可用（名字、功能描述、参数格式）
2. 模型如果认为需要，就在回复中输出一个"我想调用 XX 工具，参数是 YY"的**结构化请求**
3. **你的代码**真正执行这个工具，把结果发回给模型
4. 模型基于结果继续回答

### 2.2 定义一个工具

工具用 JSON Schema 描述（还记得 Pydantic 吗？思路完全一样）：

```python
tools = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",   # 模型靠它决定何时用
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name, e.g. Paris",
                },
            },
            "required": ["location"],
        },
    }
]
```

> **要点**：`description` 写得越清楚，模型用得越准。
> 最佳实践是写明**什么时候该用**这个工具，而不只是它是什么。

### 2.3 手写 Agent 循环（理解原理必看）

```python
import anthropic

client = anthropic.Anthropic()

def get_weather(location: str) -> str:
    """你的真实实现——查天气 API、查数据库都行，这里写死做演示。"""
    return f"Sunny, 22°C in {location}"

messages = [{"role": "user", "content": "What's the weather in Paris?"}]

while True:
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=16000,
        tools=tools,
        messages=messages,
    )

    # stop_reason 告诉我们模型为什么停：end_turn = 回答完了
    if response.stop_reason != "tool_use":
        break

    # 模型想调用工具：把模型的回复原样加入历史
    messages.append({"role": "assistant", "content": response.content})

    # 执行每个工具调用，收集结果
    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            result = get_weather(**block.input)      # 真正执行
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,             # 必须对应上
                "content": result,
            })

    # 工具结果作为 user 消息发回，进入下一轮循环
    messages.append({"role": "user", "content": tool_results})

# 打印最终回答
for block in response.content:
    if block.type == "text":
        print(block.text)
```

这个 while 循环就是**一切 Agent 框架的本质**。LangChain、LangGraph 等框架做的事情，
核心都是把这个循环包装得更好用。

### 2.4 用 SDK 的 Tool Runner 自动跑循环

官方 SDK 提供了自动化封装——用装饰器定义工具，循环交给 SDK：

```python
import anthropic
from anthropic import beta_tool

client = anthropic.Anthropic()

@beta_tool
def get_weather(location: str) -> str:
    """Get current weather for a location.

    Args:
        location: City name, e.g. Paris.
    """
    return f"Sunny, 22°C in {location}"    # 工具 schema 从函数签名自动生成！

runner = client.beta.messages.tool_runner(
    model="claude-opus-4-8",
    max_tokens=16000,
    tools=[get_weather],
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
)

for message in runner:      # 自动执行工具、喂回结果，直到任务完成
    print(message)
```

---

## 3. MCP（Model Context Protocol）

### 3.1 解决什么问题？

想让 Agent 连接 GitHub、Slack、Notion、数据库……每家的 API 都不一样，
每个 Agent 应用都要重复写一遍对接代码。

**MCP 是一个开放协议（由 Anthropic 发起），把"工具/数据源"的接入方式标准化**——
类似 USB：设备厂商按 USB 标准做接口，任何电脑都能即插即用。

```
没有 MCP:  每个 App × 每个服务 = 都要单独写对接代码（M × N 问题）

有了 MCP:
   Agent 应用 ──(MCP 协议)──▶ GitHub MCP Server   （GitHub 官方维护）
              ──(MCP 协议)──▶ Slack MCP Server    （Slack 官方维护）
              ──(MCP 协议)──▶ 你自己写的 MCP Server（暴露你的数据库/接口）
```

### 3.2 核心概念

| 概念 | 说明 |
|---|---|
| **MCP Server** | 提供能力的一方：暴露一组工具（tools）、资源（resources）、提示词（prompts） |
| **MCP Client** | 使用能力的一方：Agent 应用（如 Claude Code、你写的程序） |
| **传输方式** | 本地进程（stdio）或远程 HTTP（如 `https://mcp.linear.app/mcp`） |

### 3.3 在 API 中直接使用远程 MCP Server

Claude API 支持服务端直连 MCP Server——声明地址即可，连接由 API 侧完成：

```python
response = client.beta.messages.create(
    model="claude-opus-4-8",
    max_tokens=16000,
    betas=["mcp-client-2025-11-20"],                 # beta 功能标记
    mcp_servers=[{
        "type": "url",
        "url": "https://example.com/mcp",            # MCP Server 地址
        "name": "example-mcp",
    }],
    tools=[{
        "type": "mcp_toolset",
        "mcp_server_name": "example-mcp",            # 引用上面的 name
    }],
    messages=[{"role": "user", "content": "Use the available tools"}],
)
```

> **要点**：`mcp_servers` 声明"连哪里"，`mcp_toolset` 声明"允许模型用它的工具"，
> 两者必须成对出现。模型会自动发现该 Server 上有哪些工具并按需调用。

### 3.4 什么时候自己写 MCP Server？

当你想把**自己的服务**（比如你学的 FastAPI 后端、你的 SQLite 数据）暴露给任意 Agent 使用时。
用官方 `mcp` Python SDK 写一个 Server 大致长这样（了解即可）：

```python
# pip install "mcp[cli]"
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-todos")             # 和 FastAPI 的写法风格很像！

@mcp.tool()
def list_todos() -> list[dict]:
    """List all todo items from the database."""
    ...   # 这里可以查询你的 SQLite

if __name__ == "__main__":
    mcp.run()
```

---

## 4. Skill（技能）

### 4.1 是什么？

**Skill = 一个文件夹，装着某类任务的"操作手册"**（指令、脚本、参考资料），
Agent 在遇到相关任务时按需加载。

对比记忆：

| 概念 | 本质 | 类比 |
|---|---|---|
| Tool | 模型可以调用的**函数** | 给了 Agent 一把螺丝刀 |
| MCP | 连接工具/数据源的**标准协议** | 统一的 USB 接口 |
| Skill | 教模型怎么做某类任务的**知识包** | 一本《维修手册》 |

### 4.2 结构

一个 Skill 就是一个包含 `SKILL.md` 的文件夹：

```
my-skill/
├── SKILL.md          # 必需：主说明文件（含元数据 + 指令）
├── references/       # 可选：参考资料
└── scripts/          # 可选：配套脚本
```

`SKILL.md` 的开头是元数据（frontmatter），关键是 `description`：

```markdown
---
name: sql-report
description: 当用户要求生成数据库统计报表时使用。包含标准 SQL 模板和格式规范。
---

# SQL 报表生成规范

1. 统计查询一律使用 COUNT/SUM/AVG 聚合函数...
2. 输出格式为 Markdown 表格...
```

### 4.3 渐进式加载（Progressive Disclosure）

Skill 的关键设计：**平时只有 `description` 这一行在模型的上下文里**。
模型判断当前任务相关时，才去读取完整的 SKILL.md 和附带文件。
这样可以挂载几十个 Skill 而不撑爆上下文窗口。

> Claude API（配合代码执行容器）、Claude Code、Managed Agents 都支持 Skill。
> 官方提供了 `xlsx` / `docx` / `pptx` / `pdf` 等预置 Skill（生成 Excel、Word、PPT、PDF 文件）。

---

## 5. LangChain

### 5.1 是什么？

**LangChain 是最流行的第三方 LLM 应用开发框架**（Python / JS），提供：

- 统一的模型接口（换模型供应商只改一行）
- 提示词模板（PromptTemplate）
- 链式编排（把多个步骤"管道"起来）
- 工具、记忆、RAG 检索等常用组件

```bash
pip install langchain langchain-anthropic
```

### 5.2 基本调用

```python
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-opus-4-8")   # 读取 ANTHROPIC_API_KEY 环境变量

response = model.invoke("What is the capital of France?")
print(response.content)     # Paris
```

### 5.3 LCEL：用 `|` 把步骤串成链

LangChain 的核心语法叫 **LCEL**（LangChain Expression Language）——
用管道符 `|` 组合"提示词模板 → 模型 → 输出解析器"：

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_anthropic import ChatAnthropic

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a translator. Translate to {language}."),
    ("user", "{text}"),
])
model = ChatAnthropic(model="claude-opus-4-8")
parser = StrOutputParser()          # 把模型回复解析成纯字符串

chain = prompt | model | parser     # ★ 链！数据从左往右流

result = chain.invoke({"language": "French", "text": "Good morning!"})
print(result)    # Bonjour !
```

> **要点**：`chain.invoke()` 一次执行整条链；还有 `chain.stream()`（流式）和
> `chain.batch()`（批量）。这种"组件拼装"思想是 LangChain 的精髓。

### 5.4 定义工具

```python
from langchain_core.tools import tool

@tool
def get_weather(location: str) -> str:
    """Get current weather for a location."""    # docstring 就是工具描述
    return f"Sunny, 22°C in {location}"

# 绑定到模型：模型就"知道"了这个工具的存在
model_with_tools = model.bind_tools([get_weather])

response = model_with_tools.invoke("What's the weather in Paris?")
print(response.tool_calls)
# [{'name': 'get_weather', 'args': {'location': 'Paris'}, 'id': '...'}]
```

注意：`bind_tools` 只让模型**输出**调用请求，真正执行和循环需要你自己写——
或者交给下一节的 LangGraph。

---

## 6. LangGraph

### 6.1 是什么？

**LangGraph 是 LangChain 团队推出的 Agent 编排框架**，把 Agent 建模为**状态图（State Graph）**：

- **State（状态）**：一个共享的数据结构（如消息列表），贯穿全程
- **Node（节点）**：一个处理步骤（调用模型、执行工具、自定义逻辑）
- **Edge（边）**：节点之间的走向，可以是固定的，也可以**按条件分支**——这就实现了循环和判断

LangChain 的链是**单向直线**，LangGraph 的图可以**分支、循环、回退**——
这正是 Agent"边干边决定"所需要的。

```bash
pip install langgraph langchain-anthropic
```

### 6.2 最快的方式：预置的 ReAct Agent

```python
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool

@tool
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    return f"Sunny, 22°C in {location}"

model = ChatAnthropic(model="claude-opus-4-8")

# 一行创建完整的 Agent（含工具执行 + 循环）
agent = create_react_agent(model, tools=[get_weather])

result = agent.invoke(
    {"messages": [("user", "What's the weather in Paris?")]}
)
print(result["messages"][-1].content)
```

`create_react_agent` 内部就是第 2.3 节那个手写循环的图版本：
**模型节点 ⇄ 工具节点** 来回走，直到模型不再请求工具。

### 6.3 手动构图（理解 LangGraph 的本质）

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# 1. 定义状态：整个图共享的数据
class State(TypedDict):
    text: str
    word_count: int

# 2. 定义节点：普通函数，输入状态 → 返回要更新的字段
def count_words(state: State) -> dict:
    return {"word_count": len(state["text"].split())}

def report(state: State) -> dict:
    print(f"'{state['text']}' has {state['word_count']} words")
    return {}

# 3. 组装图
graph = StateGraph(State)
graph.add_node("count", count_words)
graph.add_node("report", report)
graph.add_edge(START, "count")      # 起点 → count
graph.add_edge("count", "report")   # count → report
graph.add_edge("report", END)       # report → 终点

app = graph.compile()
app.invoke({"text": "hello world from langgraph", "word_count": 0})
# 'hello world from langgraph' has 4 words
```

### 6.4 条件边：图的"if 语句"

Agent 循环的关键——**根据状态决定下一步走哪个节点**：

```python
def should_continue(state: State) -> str:
    """路由函数：返回下一个节点的名字。"""
    if state["word_count"] > 3:
        return "report"       # 走 report 节点
    return END                # 直接结束

graph.add_conditional_edges("count", should_continue)
```

有了条件边 + 从工具节点连回模型节点的边，就构成了完整的 Agent 循环。
LangGraph 还内置了**checkpoint（状态持久化）**、**human-in-the-loop（人工审批）**、
**多 Agent 协作**等进阶能力——这些是它相比手写循环的真正价值。

---

## 7. 概念总结与选型

### 7.1 一张图记住所有概念

```
                        ┌──────── Agent 应用 ────────┐
                        │                            │
   Skill ──(知识包)──▶  │   LLM ⇄ Agent 循环 ⇄ 工具   │ ◀──(协议)── MCP Server
   "怎么做"              │  (思考)   (编排)    (动手)   │             "连什么"
                        └────────────────────────────┘
                                     ▲
                         编排层的三种实现方式：
                         ① 手写循环（直接用 anthropic SDK）
                         ② LangChain（链式，适合固定流程）
                         ③ LangGraph（状态图，适合复杂 Agent）
```

### 7.2 选型建议

| 场景 | 推荐 | 理由 |
|---|---|---|
| 学习原理 / 简单应用 | **直接用官方 SDK** | 无额外抽象，出问题好排查，本章 2.3 的循环就够用 |
| 固定流程的 LLM 管道（翻译→摘要→存库） | **LangChain（LCEL）** | 管道语法简洁，组件丰富 |
| 复杂 Agent（循环、分支、人工审批、多 Agent） | **LangGraph** | 状态图天然表达这些结构，自带持久化 |
| 想让 Agent 用第三方服务（GitHub/Slack…） | **MCP** | 不用自己写对接，用现成 Server |
| 让 Agent 掌握你的领域规范 | **Skill** | 按需加载知识，不占常驻上下文 |

> **给初学者的路线**：先把 2.3 的手写循环完全弄懂（这是内功），
> 再学 LangGraph 的 `create_react_agent`（这是现代工程实践），
> LangChain 的 LCEL 顺手学即可，MCP 和 Skill 在需要时查文档。

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `AuthenticationError` / 401 | API key 没设置或无效 | `export ANTHROPIC_API_KEY=...`，确认 key 有效 |
| 模型不调用你的工具 | `description` 太模糊 | 写清楚"什么时候该用这个工具" |
| `tool_use_id` 相关 400 错误 | tool_result 没有对应模型发出的 tool_use id | 每个 tool_use 块都必须有一个 id 匹配的 tool_result |
| Agent 死循环、烧 token | 循环没有退出条件 | 检查 `stop_reason`；给循环加最大轮数限制 |
| 并行工具调用后报错 | 多个 tool_result 拆到了多条消息里 | 所有 tool_result 必须放在**同一条** user 消息里 |
| LangChain 导入报错 | 包拆分了，路径不对 | 模型类在 `langchain_anthropic`，模板在 `langchain_core.prompts` |
| LangGraph 节点不更新状态 | 节点函数忘了 return 字典 | 节点必须返回 `{"字段": 新值}` 形式的更新 |

---

## 小练习

1. 用官方 SDK 手写一个带 `calculator(expression: str)` 工具的 Agent 循环，
   让模型回答 "What is 123 * 456 + 789?"（工具内部用 Python `eval` 计算——仅练习用）。
2. 用 LCEL 写一条链：输入中文 → 翻译成英文 → 再统计单词数（提示：两个 prompt + 自定义函数节点）。
3. 用 `create_react_agent` 复现练习 1，对比两种写法的代码量。
4. （思考题）你的 Todo API（demo 项目）如果要暴露给 Agent 使用，
   是该写成 Tool、MCP Server 还是 Skill？为什么？
   <details><summary>参考思路</summary>
   核心是"可调用的操作"→ Tool 最直接；如果想让任意 Agent 应用（不只你自己的代码）都能用 → 包成 MCP Server；Skill 适合的是"操作规范/知识"而非接口本身。
   </details>

---

## 延伸资源

- Anthropic Agent 设计指南：<https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
- MCP 官方文档：<https://modelcontextprotocol.io/>
- LangChain 文档：<https://python.langchain.com/>
- LangGraph 文档：<https://langchain-ai.github.io/langgraph/>

> 🎉 学完本章，你已经具备了「后端 API + AI Agent」的完整知识地图——
> 这两者结合（比如给你的 FastAPI 应用加上 AI 能力）正是当下最有价值的全栈技能之一。
