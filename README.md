# r0-skills

本仓库用于维护一组 `r0-*` 本地技能，面向 Codex / Claude Code 的工程实施、代码阅读、需求收敛、架构梳理、后端约束、代码审查、提交流程与写作交付等场景。

它的目标不是堆很多零散 prompt，而是维护一套可安装、可同步、可演进、带共享契约的本地 skill 体系。

## 项目定位

- 以 `r0-*` 目录作为 skill 源目录。
- 以 `shared/` 保存跨 skill 的统一契约。
- 以 `scripts/` 保存安装同步与仓库级校验脚本。
- 以仓库根目录下的 `r0/` 保存本地执行记录、坏例子、研究笔记与阶段产物。

命名上有两层约定，不要混淆：

- skill 调用名、skill 目录名、安装软链名继续使用 `r0-xxx`
- 本地产物目录统一使用 `r0/xxx`

例如：

- `r0-request` 的本地记录目录是 `./r0/request/`
- `r0-review` 的本地记录目录是 `./r0/review/`
- `r0-work` 的本地记录目录是 `./r0/work/`

## 当前目录结构

当前仓库包含以下一级目录：

- `shared/`
- `scripts/`
- `r0-diagram-guard/`
- `r0-ios-agents/`
- `r0-question/`
- `r0-read/`
- `r0-request/`
- `r0-restrict/`
- `r0-review/`
- `r0-roadmap/`
- `r0-skill-man/`
- `r0-submit/`
- `r0-work/`
- `r0-write-lark/`
- `r0-writer/`

其中：

- `shared/r0-core-contract.md` 是当前 skill 体系的共享契约入口
- `scripts/check_skill_links.sh` 负责校验本地安装根中的 `r0-*` 软链状态
- `scripts/sync_skill_links.sh` 负责同步 skill 到 `~/.codex/skills` 与 `~/.claude/skills`
- `scripts/sync_all_remotes.sh` 负责在仓库层同步 Git 远端

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

### 2. 一键同步到本地 skill 安装目录

```bash
./scripts/sync_skill_links.sh
```

默认行为：

- 同步到 `~/.codex/skills`
- 同步到 `~/.claude/skills`
- 对来源完整性做预检查
- 对失效链接和同名入口做防护

常用参数：

```bash
./scripts/sync_skill_links.sh --pull
./scripts/sync_skill_links.sh --allow-partial
```

说明：

- `--pull`：同步前先拉取最新仓库内容
- `--allow-partial`：明确允许只同步当前仓库中的部分 `r0-*` skill

### 3. 验证安装状态

```bash
./scripts/check_skill_links.sh
ls -l ~/.codex/skills | rg 'r0-'
ls -l ~/.claude/skills | rg 'r0-'
```

如果 `check_skill_links.sh` 报来源不完整、数量异常或存在失效软链，应先修复 skill 根目录或安装根，再决定是否继续同步。

### 4. 手动同步方式

仅当脚本不可用时使用：

```bash
mkdir -p ~/.codex/skills ~/.claude/skills
for d in r0-*; do
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

## Skill 地图

### 工程实施与提交流程

| Skill | 作用 |
| --- | --- |
| `r0-request` | 把自然语言需求压成结构化 DSL，并落盘到 `./r0/request/`。 |
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
