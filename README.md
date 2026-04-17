# r0-skills

这是一个本地 skill 仓库，主要给 Codex / Claude Code 用。

仓库里放的是一组按场景拆开的 `r0-*` skills，比如需求整理、代码实施、后端约束、代码审查、提交收尾、写作交付。除了 skill 本身，这里也放了共享契约、安装脚本、同步脚本和一些本地记录规范。

## 项目定位

- `r0-*` 目录是各个 skill 的源码目录。
- `shared/` 放跨 skill 复用的统一契约。
- `scripts/` 放安装、同步、初始化和校验脚本。
- 仓库根目录下的 `r0/` 放本地执行记录、坏例子、研究笔记和阶段产物。

命名上有两层约定：

- skill 调用名、skill 目录名、安装软链名用 `r0-xxx`
- 本地产物目录用 `r0/xxx`

例如：

- `r0-request` 的本地记录目录是 `./r0/request/`
- `r0-review` 的本地记录目录是 `./r0/review/`
- `r0-work` 的本地记录目录是 `./r0/work/`

## Skill 地图

### 工程实施与提交流程

| Skill | 作用 |
| --- | --- |
| `r0-request` | 把自然语言需求压成结构化 DSL，并落盘到 `./r0/request/`；其价值在于把需求改写成更贴近 controller / planner 风格的执行契约，从而更容易驱动模型进入“计划 -> 执行 -> 校验 -> 更新状态”的工作流。 |
| `r0-restrict` | 作为后端方案约束层，从数据流、IO、组件依赖三维做后端门禁，并可渐进式嵌入 `r0-request`、`r0-work`、`r0-review`。 |
| `r0-work` | 长时间工程实施 skill，强调范围锁定、控制循环、验证、修复与交付闭环。 |
| `r0-review` | 结构化代码审查与风险分析 skill，用于 review、回归检查与问题沉淀。 |
| `r0-submit` | 提交与推送安全收尾 skill，用于 scope 校验、review-before-push、提交记录与安全调用 `r0push`。 |

### 代码阅读与架构理解

| Skill | 作用 |
| --- | --- |
| `r0-roadmap` | 阅读目录 / 仓库架构，输出模块职责、功能流和 roadmap 文档。 |
| `r0-read` | 只读型代码阅读 skill，用结构化方式理解入口、控制路径和数据流。 |
| `r0-question` | 中文知识问答与问题澄清 skill，适合梳理概念、约束、疑点与取舍。 |

### 运营与专项场景

| Skill | 作用 |
| --- | --- |
| `r0-skill-man` | skill 生态治理与日常维护。 |
| `r0-diagram-guard` | 针对 writing 项目中的流程图资产做门禁、修复与报告。 |
| `r0-ios-agents` | iOS 任务总编排器，适合多 skill 协同、并行 lane 和阶段化落地。 |
| `r0-write-lark` | 本地文章目录同步到 Lark/飞书云文档，当前稳定能力偏同步前检查与计划输出。 |
| `r0-writer` | 面向公众号长文与项目化写作的文章交付 skill。 |

### 仓库入口

- `shared/r0-core-contract.md` 是当前 skill 体系的共享契约入口
- `scripts/install_and_quick_start.sh` 负责“拉取远端 + quick start”一键配置安装
- `scripts/quick_start.sh` 负责命名初始化、skill 同步、链接校验与 `r0push` 固定
- `scripts/init_skill_namespace.py` 负责把仓库从 `r0-*` 改成自定义前缀
- `scripts/check_skill_links.sh` 负责校验本地安装根中的 `r0-*` 软链状态
- `scripts/sync_skill_links.sh` 负责同步 skill 到 `~/.codex/skills` 与 `~/.claude/skills`
- `scripts/sync_all_remotes.sh` 负责在仓库层同步 Git 远端
- `r0-submit/scripts/r0push` 是仓库内自带的 push 工具，会被 quick start 固定到绝对路径

## 快速开始

### 1. 克隆仓库

```bash
git clone <你的仓库地址> r0-skills
cd r0-skills
```

示例：

```bash
git clone git@gl.quanyougame.net:lynsan/skills-man.git r0-skills
cd r0-skills
```

### 2. 一键配置安装（推荐）

如果你希望先从远端拉取，再自动完成 quick start，直接运行：

```bash
./scripts/install_and_quick_start.sh
```

默认行为：

- 默认拉取远端 `github`
- 默认拉取分支 `main`
- 拉取成功后自动继续执行 `./scripts/quick_start.sh`

常用示例：

```bash
./scripts/install_and_quick_start.sh
./scripts/install_and_quick_start.sh --remote origin --name lyn
./scripts/install_and_quick_start.sh --remote cggame --branch main --allow-dirty
./scripts/install_and_quick_start.sh --dry-run
```

当前仓库已配置的三个远端是：

- `github`
- `origin`
- `cggame`

推荐顺序：

1. 首次 clone 后直接运行 `./scripts/install_and_quick_start.sh`
2. 需要切换自定义前缀时，加 `--name <your-prefix>`
3. 完成后优先使用 `$HOME/.local/bin/<prefix>push` 作为固定提交入口

### 3. 一键快速启动（本地仓库已是最新时推荐）

如果你希望一次完成命名初始化、`r0push` 固定、skill 同步和链接校验，直接运行：

```bash
./scripts/quick_start.sh
```

常用示例：

```bash
./scripts/quick_start.sh --name lyn
./scripts/quick_start.sh --name lyn --dry-run
./scripts/quick_start.sh --name lyn --allow-dirty
```

这个脚本会顺序执行：

- 命名初始化
- skill 同步到 `~/.codex/skills` 与 `~/.claude/skills`
- skill 链接校验
- 将 `r0push` 固定到绝对路径 `~/.local/bin/<prefix>push`

完成后，推荐直接使用这个绝对路径调用提交工具，例如：

```bash
$HOME/.local/bin/r0push help
```

执行命名初始化后，上面的 `r0push` 也会一起改成你的自定义前缀版本，例如 `$HOME/.local/bin/lynpush`。

### 4. 仅初始化自己的 skill 前缀（手动模式）

如果你希望把整套 `r0-*` skill 体系改成你自己的名字，先执行初始化脚本，再做本地安装同步：

```bash
python3 scripts/init_skill_namespace.py
```

默认规则：

- 优先使用 `--name <your-name>`
- 未显式传参时，尝试读取当前仓库的 Git `user.name`
- 若 `user.name` 不可用，再尝试使用 Git `user.email` 的 `@` 前缀
- 若都拿不到或清洗后为空，则回退到 `ouo`

常用示例：

```bash
python3 scripts/init_skill_namespace.py --name lyn
python3 scripts/init_skill_namespace.py --name lyn --dry-run
python3 scripts/init_skill_namespace.py --name lyn --allow-dirty
```

脚本行为：

- 自动探测当前 skill 前缀，例如 `r0`
- 批量替换仓库内文本中的前缀标识
- 重命名 `r0-*` 目录、相关脚本文件名和 `shared/r0-core-contract.md`
- 连 `r0push`、`check_r0push_scope.py` 这类 skill 内部复合命名也会一起替换成新前缀
- 把硬编码的 `/Users/r0/...` 路径收敛为 `$HOME/...`，避免克隆到别的机器后仍残留作者本地路径

默认会阻止在 dirty worktree 上直接执行，避免误改你已经有本地变更的仓库；如果你明确知道自己在做什么，再显式加 `--allow-dirty`。

`r0push` 现在也作为仓库内工具提供，位置是 `./r0-submit/scripts/r0push`；执行初始化后，这个脚本也会一起改名成你的自定义前缀版本。

### 5. 一键同步到本地 skill 安装目录

```bash
./scripts/sync_skill_links.sh
```

默认行为：

- 同步到 `~/.codex/skills`
- 同步到 `~/.claude/skills`
- 自动探测当前 skill 前缀，不再写死只能处理 `r0-*`
- 对来源完整性做预检查
- 对失效链接和同名入口做防护

常用参数：

```bash
./scripts/sync_skill_links.sh --pull
./scripts/sync_skill_links.sh --allow-partial
```

说明：

- `--pull`：同步前先拉取最新仓库内容
- `--allow-partial`：明确允许只同步当前仓库中的部分 `<prefix>-*` skill

### 6. 验证安装状态

```bash
./scripts/check_skill_links.sh
find ~/.codex/skills -maxdepth 1 -mindepth 1 -type l | sort
find ~/.claude/skills -maxdepth 1 -mindepth 1 -type l | sort
```

如果 `check_skill_links.sh` 报来源不完整、数量异常或存在失效软链，应先修复 skill 根目录或安装根，再决定是否继续同步。

### 7. 手动同步方式

仅当脚本不可用时使用：

```bash
mkdir -p ~/.codex/skills ~/.claude/skills
prefix="$(basename "$(ls shared/*-core-contract.md | head -n 1)")"
prefix="${prefix%-core-contract.md}"
for d in "${prefix}"-*; do
  ln -sfn "$(pwd)/$d" ~/.codex/skills/"$d"
  ln -sfn "$(pwd)/$d" ~/.claude/skills/"$d"
done
```

手动方式只适用于“当前仓库就是完整 skill 根目录”的场景；如果这是 worktree、镜像或裁剪仓库，不要直接批量重建链接。

## 在 Codex / Claude Code 中使用

### Codex

建议在提示词开头显式写 skill 名，例如：

- `$r0-roadmap 阅读这个仓库，输出架构、模块边界和主流程。`
- `$r0-request 把这个需求整理成可执行 DSL，并写入 ./r0/request/。`
- `$r0-restrict 约束这份后端技术方案，重点审视数据流、IO 和依赖。`
- `$r0-work 完成这个需求，改动范围限制在 api 和 service 层。`
- `$r0-review`
- `$r0-submit`
- `$r0-writer 把我的资料整理成一篇公众号长文，并补齐 outline、style 和 draft。`

### Claude Code

Claude Code 侧通常用 slash command 风格：

- `/r0-roadmap 阅读这个目录，输出架构与功能边界。`
- `/r0-request 把我的需求整理成结构化提示词 DSL。`
- `/r0-restrict 约束当前后端技术方案，输出主要风险与门禁点。`
- `/r0-work 完成这个需求，范围限制在 api 和 service 层。`
- `/r0-review`
- `/r0-submit`

如果你已经打开了 Codex 或 Claude Code，但会话里看不到新 skill，通常重开一次会话即可。

## 推荐工作流

### 新项目默认顺序

推荐先建立上下文，再进入实现：

1. `r0-roadmap`
2. `r0-question`
3. `r0-work` 或 `r0-request -> r0-work`

目的：

- 先建立项目结构认知
- 再确认问题边界
- 最后进入实现与验证

### 需求分流规则

- 小需求、边界清楚：直接 `r0-work`
- 中大型需求、容易跑偏：先 `r0-request`，再 `r0-work`
- 后端方案、架构门禁、技术评审：显式加入 `r0-restrict`
- 改完后要看风险或回归：接 `r0-review`
- 真正交付收尾：最后必须经过 `r0-submit`

典型链路：

- 小需求：`r0-roadmap -> r0-question -> r0-work -> r0-submit`
- 复杂需求：`r0-roadmap -> r0-question -> r0-request -> r0-work -> r0-submit`
- 后端方案：`r0-question -> r0-restrict -> r0-request -> r0-work`
- 提交前质量门：`r0-work -> r0-review -> r0-submit`

### `r0-request` 的行为影响边界

`r0-request` 的作用是把一个松散需求整理成强结构的执行契约。它最直接的价值是让后续模型更容易按“先规划、再执行、再校验”的方式工作，而不是一上来就自由发挥。

这类 DSL 通常会带来几个稳定效果：

- 让任务范围更清楚，不容易一路扩需求
- 让阶段、依赖和验证标准更明确
- 让模型更容易进入计划式、控制器式的执行风格

但边界也要写清：

- 它影响的是模型行为倾向，不是宿主权限
- 它不能把自己“伪装成内部角色”
- 它也不能凭空开启宿主没有提供的计划模式、工具能力或其他内置功能

更准确的理解是：

- 如果宿主本来就支持计划模式、工具调用或阶段化执行，`r0-request` 产出的 DSL 更容易和这些能力对齐
- 如果宿主不支持这些能力，DSL 仍然有价值，但价值主要体现在结构化约束，而不是功能解锁

### `r0-restrict` 在体系里的位置

`r0-restrict` 不是一个通用执行器，而是一个后端约束层：

- 单独调用时：用于约束后端技术方案和技术评审
- 被 `r0-request` 调用时：把后端约束嵌入已有 DSL 字段，不新增模板章节
- 被 `r0-work` 调用时：在实现前建立数据流、IO、依赖三维门禁
- 被 `r0-review` 调用时：作为后端 review 的风险词典

它当前只覆盖后端和 To-C 后端约束，不承担前端限制层、客户端矩阵或安全平台脚本。

## 共享契约与本地记录

所有 `r0-*` skill 都应遵守 `shared/r0-core-contract.md`。当前统一约束包括：

- 执行结果遵循统一摘要卡片与结构化输出约定
- 本地记录统一落到 `./r0/<skill-key>/`
- `r0/` 默认不进入版本控制
- 若本地记录被误加入暂存区，统一使用：

```bash
git restore --staged -- r0/ 'r0-*'
```

如果目标项目里还存在历史 `r0-xxx/` 记录目录，应先执行迁移：

```bash
python3 /Users/r0/.codex/skills/r0-submit/scripts/migrate_r0_record_dirs.py --repo-root .
```

## 更新与同步远端

仓库更新后，推荐直接重新同步本地 skill：

```bash
cd /path/to/r0-skills
./scripts/sync_skill_links.sh --pull
```

如果需要把当前 Git 分支同步到多个远端：

```bash
./scripts/sync_all_remotes.sh
./scripts/sync_all_remotes.sh --remote origin --remote github
./scripts/sync_all_remotes.sh --branch main
```

说明：

- 脚本会先检查当前仓库是否像一个“完整 skill 来源”
- 若工作树中存在本地 skill 目录，但尚未纳入 Git tracked scope，预检可能把它视为 partial source
- 若明确只想同步当前仓库已追踪的范围，可使用：

```bash
./scripts/sync_all_remotes.sh --branch main --allow-partial-scope
```

## 维护原则

- 优先维护共享契约，不要让不同 skill 各自漂移
- 优先做渐进式披露，不要把所有细则都塞进主 `SKILL.md`
- 优先把可复用的约束沉淀到对应 `r0/xxx/` 本地记录目录
- 优先用已有脚本和既有约定，不要为局部问题引入新工具链
- skill 的职责应清晰收敛，避免把一个 skill 扩成“大而全 orchestrator”

## 何时更新 README

以下情况应同步更新本 README：

- 新增或删除一级 `r0-*` skill
- 某个 skill 的职责发生明显变化
- 安装 / 同步 / 校验脚本的默认行为发生变化
- 共享契约的核心规则变化到会影响使用者心智模型

README 的职责是解释“这套 skill 体系是什么、怎么装、怎么用、怎么维护”，不是复制每个 `SKILL.md` 的全部细节。具体执行规则应回到各自 skill 文档中查看。
