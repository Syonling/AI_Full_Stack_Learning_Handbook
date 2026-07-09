# 02 · Git 版本控制入门

> 本章目标：学会用 Git 记录代码的每一次变化，敢改代码、敢做实验——因为随时可以回退。
> 预计学习时间：2~3 小时。无前置知识要求，学完立刻就能用在你的所有练习上。

---

## 学习目标

1. 理解版本控制解决什么问题
2. 掌握核心工作流：`init → add → commit`，以及 `status / log / diff`
3. 会写 `.gitignore`（哪些文件不该进版本库）
4. 会用分支做实验：`branch / switch / merge`
5. 会撤销错误：改错了文件、commit 错了怎么办
6. 会把代码推送到 GitHub

---

## 1. 为什么需要版本控制？

没有 Git 的世界：

```
main.py
main_备份.py
main_最终版.py
main_最终版2_真的不改了.py     ← 你一定见过这种文件夹
```

Git 帮你解决三件事：

1. **历史记录**：每次提交都是一个快照，任何时候能回到任何版本
2. **敢于实验**：开个分支随便改，改砸了一键丢弃
3. **协作与备份**：推送到 GitHub，代码永不丢失，也方便与人协作

> macOS 自带 Git。终端输入 `git --version` 确认（如提示安装开发者工具，按提示装即可）。

首次使用先设置身份（提交记录上会显示是谁改的）：

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

---

## 2. 核心工作流：init → add → commit

Git 的三个区域，理解了它就理解了一半：

```
工作区（你正在编辑的文件）
   │  git add        （挑选要保存的改动）
   ▼
暂存区（staging：本次快照要包含的内容）
   │  git commit     （拍快照，写说明）
   ▼
版本库（.git 文件夹：所有历史快照）
```

```bash
cd my_project
git init                        # 1. 把当前文件夹变成 Git 仓库（只做一次）

git status                      # 2. 随时查看：哪些文件改了、哪些已暂存

git add main.py                 # 3. 暂存指定文件
git add .                       # 或暂存所有改动（最常用）

git commit -m "add todo list api"    # 4. 提交快照 + 一句话说明
```

日常节奏就是：**改代码 → `git add .` → `git commit -m "..."`**，一个小功能一次提交。

### 查看历史与差异

```bash
git log --oneline               # 简洁历史：每次提交一行
git log                         # 完整历史（q 退出）

git diff                        # 工作区 vs 上次提交：改了什么还没暂存
git diff --staged               # 暂存区 vs 上次提交：即将提交什么
git show                        # 看最近一次提交改了什么
```

> **要点**：`git status` 是你的"仪表盘"，不确定当前状态时先敲它，它还会提示你下一步可用的命令。

---

## 3. .gitignore：哪些东西不进版本库

有些文件**不该**被 Git 跟踪：虚拟环境（几十 MB 且可重建）、数据库文件、密钥、缓存。
在仓库根目录建一个 `.gitignore` 文件：

```gitignore
# Python
.venv/
__pycache__/
*.pyc

# 数据库文件（数据不进版本库，结构靠代码里的建表语句）
*.db
*.sqlite3

# 密钥与本地配置（第 08 章详讲——泄露 API key 后果严重！）
.env

# 编辑器 / 系统
.vscode/
.DS_Store
```

> **要点**：`.gitignore` 只对**还没被跟踪**的文件生效。
> 如果已经把 `.venv` 提交进去了，先 `git rm -r --cached .venv` 再提交一次。

### 好的 commit message

```bash
# ✅ 好：说清楚"做了什么"
git commit -m "add DELETE /todos/{id} endpoint"
git commit -m "fix: return 404 when todo not found"

# ❌ 差：等于没说
git commit -m "update"
git commit -m "改了点东西"
```

---

## 4. 分支：安全的实验场

分支 = 平行世界。在分支上随便改，主线（main）不受影响；满意了合并回来，不满意直接删掉。

```bash
git branch                      # 查看所有分支（* 标记当前所在分支）

git switch -c add-search        # 创建并切换到新分支（-c = create）
# ... 在这个分支上写代码、正常 add/commit ...

git switch main                 # 切回主分支（刚才的改动"消失"了——它们在另一个世界）
git merge add-search            # 把实验分支的成果合并进 main

git branch -d add-search        # 合并完删掉分支
```

### 合并冲突（conflict）不可怕

两个分支改了**同一行**时，Git 不知道听谁的，会把两个版本都写进文件让你选：

```
<<<<<<< HEAD
title = "我的待办"          ← main 分支的版本
=======
title = "Todo List"        ← 你分支的版本
>>>>>>> add-search
```

处理：编辑文件，留下你要的内容，删掉 `<<<<<<<` `=======` `>>>>>>>` 标记，然后 `git add .` + `git commit`。

---

## 5. 后悔药：撤销操作

| 场景 | 命令 | 说明 |
|---|---|---|
| 改乱了一个文件，想恢复到上次提交 | `git restore main.py` | ⚠️ 未提交的修改会丢失 |
| add 错了，想从暂存区拿出来 | `git restore --staged main.py` | 文件内容不变，只是取消暂存 |
| commit 说明写错了 | `git commit --amend -m "新说明"` | 修改最近一次提交 |
| 想撤销最近一次 commit（保留改动） | `git reset --soft HEAD~1` | 改动回到暂存区，可重新提交 |
| 想看某个历史版本的文件 | `git show 提交号:main.py` | 提交号用 `git log --oneline` 查 |

> **要点**：只要**提交过**，几乎任何东西都找得回来。所以：多提交、小步提交。
> 最危险的是 `git reset --hard`——它会丢弃未提交的改动，新手阶段别用。

---

## 6. GitHub：远程备份与展示

GitHub 是托管 Git 仓库的网站（类似"代码的网盘 + 社交"）。流程：

1. 在 <https://github.com> 注册并新建仓库（Create repository，**不要**勾选自动生成 README）
2. 按页面提示把本地仓库关联上去：

```bash
git remote add origin https://github.com/你的用户名/仓库名.git
git branch -M main              # 确保主分支叫 main
git push -u origin main         # 首次推送（-u 记住对应关系）

# 之后每次只需：
git push                        # 推送新提交到 GitHub
git pull                        # 拉取远程的新提交（换电脑/协作时用）
```

克隆别人的（或自己另一台电脑上的）仓库：

```bash
git clone https://github.com/用户名/仓库名.git
```

> 推送时 GitHub 会要求登录。推荐用 **Personal Access Token**（Settings → Developer settings → Tokens）
> 或安装 [GitHub CLI](https://cli.github.com/)（`brew install gh` 然后 `gh auth login`），比密码方便。

---

## 常见错误与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `fatal: not a git repository` | 当前目录不是仓库 | `cd` 到项目根目录，或先 `git init` |
| `nothing to commit` | 忘了 `git add` | 先 `git add .` 再 commit |
| 提交里混进了 `.venv` / `.db` | 没写 `.gitignore` | 补 `.gitignore`，`git rm -r --cached 文件` 后重新提交 |
| `Please tell me who you are` | 没配置身份 | 见第 1 节的 `git config` |
| push 被拒绝 `rejected` | 远程有你本地没有的提交 | 先 `git pull`，处理可能的冲突后再 push |
| 切换分支提示会覆盖改动 | 有未提交的修改 | 先 commit（或 `git stash` 暂存起来） |

---

## 小练习

1. 把 `learning_from_claude` 的上级目录（你的整个学习项目）初始化为 Git 仓库，
   写好 `.gitignore`（忽略 `.venv/`、`*.db`、`__pycache__/`、`.env`），完成第一次提交。
2. 之后每完成一章的练习就提交一次，坚持写清楚 commit message。
3. 开一个分支 `experiment`，随便改坏一个文件并提交，然后切回 main 确认主线完好，删掉该分支。
4. 在 GitHub 建一个仓库，把你的学习项目推上去。

> 下一章：[03 · 日志与调试](03-logging-and-debugging.md) —— 让程序自己"说话"，出问题时知道去哪找。
