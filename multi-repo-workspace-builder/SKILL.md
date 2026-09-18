---
name: multi-repo-workspace-builder
description: 创建或重组多代码库开发工作区：一个独立 Git 根项目、共享文档和本地链接的独立代码库。用户要求为多个现有仓库建立统一入口、组织项目与子代码库、添加安全本地符号链接，或建立根目录及各代码库的 AGENTS.md 规则时使用。
---

# 多代码库工作区构建

建立“协调仓库 + 独立代码库”的工作区：根项目保存共享文档、决策、协作规则和链接脚本；每个子代码库仍是独立 Git 工作区。不得把子代码库源码、个人绝对路径或子代码库改动提交到根项目。

## 文档语言

默认使用与用户沟通所用语言一致的语言编写工作空间的 `README.md`、`AGENTS.md`、`docs/` 文档和链接脚本的用户可见提示。用户未明确指定语言时，以当前对话语言为准；专有名词、命令、代码标识符和用户明确要求保留的内容可保持原文。

## 收集范围并保护现状

1. 确认根工作区路径、每个代码库的本地 Git 根目录、显示名称和业务职责。用户未指定根路径时，在 `$HOME/workspace/<项目名>/` 创建工作区；用户指定其他路径时以其指定路径为准。
2. 检查根目录是否已有 `.git`；项目必须有自己的 Git 仓库。若尚未初始化且用户要求创建工作区，执行 `git init`；不要重置已有仓库。
3. 对根仓库和每个已链接代码库分别执行 `git status --short`。将所有既有修改视为用户工作。
4. 对目标为既有代码库的任务，先读取其 `AGENTS.md`。根工作区及每个子代码库都必须各有自己的 `AGENTS.md`：
   - 根 `AGENTS.md` 同时说明工作区定位、规则加载顺序、子库路由、链接、Git 保护、文档分类、事实源、索引和统一交付；
   - 子库 `AGENTS.md` 说明其代码规范、构建和测试要求。
5. 如果既有子库没有 `AGENTS.md`，且用户只授权组织根工作区，先说明缺口并请求允许后再修改该子库。不要在没有授权时把规则写入他人代码库。

## 建立根项目

创建或维护以下最小结构；可按项目实际增加文档分类，但不要复制子库源代码：

```text
workspace/
├── .git/
├── .gitignore
├── .agents/
│   └── AGENTS.md  →  ../AGENTS.md (软链接，NIO Chat 特供)
├── README.md
├── AGENTS.md
├── docs/
│   ├── README.md
│   ├── requirements/
│   ├── architecture/
│   ├── design/
│   ├── decisions/
│   ├── minutes/
│   └── reference/
└── scripts/
    └── setup-workspace-links.sh
```

在根 `README.md` 中说明每个目录的职责、代码库边界、链接初始化命令和验证命令。在 `docs/README.md` 中列出各文档分类及当前代码边界。不得创建 `docs/AGENTS.md`；所有文档规则统一维护在根 `AGENTS.md`。创建空目录时使用 `.gitkeep` 或实际索引文件，以便 Git 跟踪。

### VS Code 多根工作区

VS Code 多根工作区是本机配置，不得跟踪或提交。需要创建时，将根目录下的 `*.code-workspace` 加入 `.gitignore`（推荐 `/*.code-workspace`）；本机 workspace 的 `folders` 中先放根目录（`path: "."`），再按链接脚本的参数顺序放入各子库别名。子库路径使用相对入口路径（如 `components`），不要写入个人绝对路径。默认不设置 `name`，让 VS Code 使用目录原名；只有用户明确要求时才设置自定义显示名。保持 `settings` 为空，除非用户另有明确配置要求。

新增、移除或改名子库入口时，必须在同一次根工作区改动中同步更新链接脚本参数和 README 中的代码库边界/初始化示例；本机 workspace 存在时也应同步更新其 `folders`，但不得提交。VS Code workspace 可在链接尚未初始化时保留相对入口，以便用户完成初始化后直接打开。

### NIO Chat 特供：`.agents/AGENTS.md` 软链接

NIO Chat 运行时只会自动加载 `.agents/AGENTS.md` 作为工作区规则文件，不会读取项目根目录下的 `AGENTS.md`。为了让根 `AGENTS.md` 中的规则真正生效，新建工作区时必须：

1. 创建 `.agents` 目录：`mkdir -p .agents`
2. 创建软链接：`ln -s ../AGENTS.md .agents/AGENTS.md`
3. 在根 `AGENTS.md` 开头注明：`.agents/AGENTS.md` 是指向本文件的软链接，供 NIO Chat 运行时自动加载使用，规则维护以根 `AGENTS.md` 为唯一事实源。

根 `AGENTS.md` 保持唯一事实源，`.agents/AGENTS.md` 通过软链接让 NIO Chat 自动加载规则，二者内容始终一致。软链接可被 Git 正常跟踪。

将本机链接别名逐项加入 `.gitignore`，例如：

```gitignore
# 系统与 IDE 临时文件
.DS_Store
.idea/

# 本地 VS Code 多根工作区。
/*.code-workspace

# NIO Chat 运行时目录（AGENTS.md 软链接会被跟踪，其他运行时产物忽略）
.agents/attachments/
.agents/history/
.agents/chunked_writes/

# 指向独立代码仓库的本地链接。
/factory-a
/shared-platform
```

`.agents/AGENTS.md` 软链接本身需要被 Git 跟踪（确保克隆后规则自动生效），所以只忽略 `.agents/` 下的运行时产物目录，不忽略整个 `.agents/`。

不要忽略通配符形式的源码目录，也不要将本地代码库的绝对路径写进受跟踪文件。

## 编写安全的链接脚本

提供 `scripts/setup-workspace-links.sh`，并遵循以下合同：

1. 接收固定顺序的子库根目录参数，并提供 `--help`。
2. 校验每个路径存在、是 Git 工作区且恰好是其 Git 根目录。
3. 仅在根工作区内创建以仓库别名命名的符号链接。
4. 可重复执行；若已有同名链接指向相同目标，保持不变。若指向其他目标，展示旧目标和新目标；仅在用户已授权该替换时更新，否则报告冲突，不覆盖。
5. 若同名路径是任何真实文件或目录，立即失败，绝不覆盖。
6. 完成后对每个链接执行 `git -C <alias> rev-parse --show-toplevel` 验证。

脚本应使用 `set -euo pipefail`、引用所有路径变量，并从脚本自身位置推导根工作区。只在用户明确提供或确认所有目标路径后执行它；不要自行搜索磁盘并绑定仓库。

## 写入跨仓库协作规则

在根 `AGENTS.md` 开头先注明 NIO Chat 规则加载机制：

> `.agents/AGENTS.md` 是指向本文件的软链接，供 NIO Chat 运行时自动加载使用。所有规则维护以根目录 `AGENTS.md` 为唯一事实源，不要直接修改 `.agents/AGENTS.md`。

在同一个根 `AGENTS.md` 中明确以下事实：

- 根项目与子代码库是独立 Git 工作区，根提交不会包含子库修改；
- 开始代码任务前显式读取目标子库的 `AGENTS.md`；跨库任务分别声明修改范围、验证和交付状态；
- 代码库链接失效或目标不匹配时，停止并索取正确路径；
- 现有修改、未跟踪文件和本地配置不可删除、覆盖、暂存或格式化；
- 仅在用户明确要求时提交、推送、清理、切换分支或修改 Git 历史；
- **目标工作区内随仓库共享的项目专用 Skill 统一放在根目录 `skills/<skill-name>/` 下，禁止放到 `.agents/skills/`**——这是本工作区的 NIO Chat 适配约定，不替代个人通用 Skill 的 `custom-skills` 源目录及用户级安装约定。项目 Skill 的实际发现或显式加载方式应按所用客户端说明；不得声称仅放入 `skills/` 就会被自动加载。

在同一个根 `AGENTS.md` 中写入文档规则：`docs/` 的分类职责、需求与代码的事实源优先级、索引同步要求、相对链接要求，以及 Markdown 变更的检查方法。不要把这些规则拆分到 `docs/AGENTS.md`。

若项目有固定主分支或共享工程规范，写入根 `AGENTS.md`，并保持子库规则仅存放差异规则。不要把一座工厂或单个产品的专属实现描述为平台共性。

## 分支与 Git worktree

解释并维护这一边界：链接脚本只选择一个本地检出目录，不管理分支。日常切换分支在实际子库中执行：

```bash
git -C <alias> status
git -C <alias> switch <branch>
```

需要同时保留多个分支时，在子库中创建 Git worktree，再将根工作区链接更新到用户指定的检出目录。新建工作分支前，先检查工作区状态、获取远端信息、以安全快进方式同步指定主分支，然后从最新主分支创建分支。不要在有未提交修改的检出目录上擅自切换分支。

## 验证与交付

完成后执行并报告：

```bash
bash -n scripts/setup-workspace-links.sh
./scripts/setup-workspace-links.sh <repo-a-root> <repo-b-root> [...]
ls -la .agents/AGENTS.md    # 验证软链接指向 ../AGENTS.md
test -z "$(git ls-files -- '*.code-workspace')"
git check-ignore -q workspace.code-workspace
git status --short --ignored
git diff --check
git -C <alias> rev-parse --show-toplevel
```

确认 `.agents/AGENTS.md` 是指向 `../AGENTS.md` 的有效软链接。代码库入口链接应被 Git 忽略；`.agents/AGENTS.md` 规则链接应未被忽略、可被 Git 跟踪。根仓库只应显示其自身的工作区文件，不应包含子库源码。交付时分别列出根项目与每个子库的改动、验证结果、未处理事项和保留的既有状态。除非用户明确要求，不创建 Git 提交。
