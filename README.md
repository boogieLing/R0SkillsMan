# skills-man

本仓库用于维护当前仍由 Git 追踪的一组 `r0-*` 本地技能，覆盖代码实现、代码阅读、提交流程与架构 roadmap 等场景。

本地执行记录、总结、坏例子与研究笔记统一落到仓库根目录下的 `r0/`，例如 `r0/request/`、`r0/review/`、`r0/work/`。
注意两层命名不要混淆：
- skill 调用名、skill 目录名、安装软链名继续使用 `r0-xxx`
- 文档产物、本地记录目录统一使用 `r0/xxx`

## 技能清单与作用

| Skill | 作用 |
| --- | --- |
| `r0-diagram-guard` | 对文章目录中的流程图资产做质量门禁与自动修复，重点处理黑块、截断、占位图、坏引用等问题，并输出门禁报告。 |
| `r0-ios-agents` | 作为 iOS 任务总编排器，按依赖关系协调多技能并行执行。 |
| `r0-question` | 中文知识问答与问题分析技能，强调分点和结构化表达。 |
| `r0-read` | 只读型代码阅读技能，用结构化方式理解项目架构与主流程。 |
| `r0-request` | 把自然语言需求转换为结构化提示词 DSL，并落盘到 `./r0/request/` 作为本地需求文档。 |
| `r0-review` | 系统化代码审查技能，围绕正确性、安全性、复杂度、可读性和可维护性输出可复核结论。 |
| `r0-roadmap` | 阅读目标目录/仓库的架构与功能流，生成 `./r0/roadmap/` 文档，并在存在时同步摘要到全局 `AGENTS.md`。 |
| `r0-skill-man` | 本地技能生态的日常维护技能，用于巡检、收敛坏例子与同步治理规则。 |
| `r0-submit` | 开发收尾提交编排技能，先审查再分组提交，使用 `r0push` 推送，并在本地记录提交过程。 |
| `r0-work` | 面向工程交付的实施技能，强调严格流程、范围控制和多语言项目下的生产级代码实现。 |
| `r0-writer` | 面向公众号长文与项目化写作的技能，把素材、笔记、链接或草稿整理成 `outline.md`、`style.md`、`draft.md` 等文章交付物，并对齐 `/Volumes/R0sORICO/writing` 的模板与 SOP。 |
| `r0-write-lark` | 将本地文章目录按自然语言指令同步到 Lark/飞书云文档。 |

当前工作树包含上表中的 skill 目录，但“可发布 / 可远端同步的受管范围”以 Git 当前实际追踪的 `r0-*` 文件为准。若你的 `~/.codex/skills` 或 `~/.claude/skills` 里还保留历史 `r0-*` 软链，执行同步前应先运行 `./scripts/check_skill_links.sh`，确认没有指向本仓库已不存在目录的失效链接。

## 推荐工作流与最佳实践

### 新项目默认顺序

对于一个新项目，推荐按下面的顺序使用 skill：

1. 先用 `r0-roadmap` 阅读项目架构、功能边界和主流程。
2. 再用 `r0-question` 把关键问题、约束、疑点和实现思路问清楚。
3. 完成上述理解后，再正式进入具体需求执行。

这样做的目的，是先建立“项目结构认知”和“问题认知”，避免一上来直接写需求实现，导致范围判断错误或改动落点不准。

### 做需求时的分流规则

进入具体需求阶段后，按任务规模决定流程：

- 如果需求较小、边界清楚、可以直接落地，可以直接进入 `r0-work`。
- 如果需求是长时间任务、复杂任务，或者需要先把目标、拆分、执行约束说清楚，先用 `r0-request` 把需求整理成结构化 DSL，再进入 `r0-work`。

推荐把这条规则理解为：

- 小需求：`r0-roadmap -> r0-question -> r0-work`
- 复杂需求：`r0-roadmap -> r0-question -> r0-request -> r0-work`

### 收尾要求

需求完成之后，必须执行 `r0-submit` 做收尾，而不是停在“代码写完”。

`r0-submit` 负责把审查、提交分组、推送与本地提交记录串起来，确保一次需求交付真正闭环。

### 常见场景实践

#### 1. 只是想先看懂项目，不急着改代码

这种场景不要一上来就 `r0-work`。

- 如果目标是建立全局认知、看架构、看功能边界，优先用 `r0-roadmap`。
- 如果目标是只读地理解代码实际怎么跑、入口在哪、数据怎么流，优先用 `r0-read`。
- 如果你已经有一轮阅读结果，但还需要把疑点、方案分歧、实现取舍问清楚，再接 `r0-question`。

可以这样理解：

- 偏“全局地图”：`r0-roadmap`
- 偏“代码实读”：`r0-read`
- 偏“问题澄清”：`r0-question`

一个常见组合是：

- `r0-roadmap -> r0-read -> r0-question`

适用于老项目接手、陌生仓库排查、动手前先做上下文建立。

#### 2. 中大型需求或容易跑偏的需求

如果需求跨模块、执行时间长、需要多轮编译验证，或者你担心口头描述太散，推荐不要直接开做。

更稳妥的顺序是：

- `r0-roadmap -> r0-question -> r0-request -> r0-work -> r0-submit`

其中：

- `r0-request` 负责把需求压成结构化 DSL，锁定范围、成功标准、任务 DAG 和验证口径。
- `r0-work` 应把这份 DSL 当执行契约，而不是重新自由发挥。

这类场景特别适合：

- 多模块改动
- 多阶段交付
- 需要反复 build / test / repair 的任务
- 容易边做边扩需求的任务

#### 3. 小需求、热修、边界很清楚的改动

如果需求很小，且范围、落点、验证方式都明确，可以跳过 `r0-request`，直接进入执行。

推荐顺序：

- `r0-roadmap -> r0-question -> r0-work -> r0-submit`

如果你对项目已经很熟，甚至可以把前置缩短成：

- `r0-question -> r0-work -> r0-submit`

但前提是你已经非常清楚改动边界，不需要再次做架构扫描。

#### 4. 改完以后不确定有没有回归，或准备提交前想做一次质量门

这时不要直接推。

- 如果重点是看 bug、回归风险、复杂度、可维护性，用 `r0-review`。
- 如果目标是把审查、分组提交、scope 检查、推送串起来，用 `r0-submit`。

推荐顺序：

- `r0-work -> r0-review -> r0-submit`

适用于：

- 中高风险改动
- 改动跨多个文件或模块
- 准备 push 前想再做一次显式风险检查
- 需要留下可复核审查记录

#### 5. 写公众号文章或长文项目

写作类任务不要硬套工程实施链路。

推荐顺序：

- `r0-writer -> r0-diagram-guard -> r0-write-lark`

其中：

- `r0-writer` 负责把素材整理成 `outline.md`、`style.md`、`draft.md`、`notes.md` 等交付物。
- `r0-diagram-guard` 负责在同步前检查并修复流程图黑块、截断、占位图、坏引用等问题。
- `r0-write-lark` 更适合作为“飞书 / Lark 同步位”的预留入口，放在文章资产和正文都相对稳定之后再接。

一个实用约束是：

- 文章里只要出现流程图，就尽量先过一遍 `r0-diagram-guard`，再做对外同步。
- 由于当前仓库中的 `r0-write-lark` 还是占位型 skill，若要把它作为稳定同步链路使用，建议先补完它的真实流程与输出契约。

#### 6. iOS 任务不是单点改一个 View，而是整条链路交付

如果是 Figma 到 SwiftUI、跨多个 lane 并行、需要门禁和阶段化验证的 iOS 工作，不要只靠单个实现 skill。

推荐把 `r0-ios-agents` 当总编排器：

- 新项目 / 新模块：`r0-roadmap -> r0-question -> r0-ios-agents`
- 复杂需求：`r0-roadmap -> r0-question -> r0-request -> r0-ios-agents -> r0-submit`

适用于：

- 端到端 iOS 功能交付
- Figma 设计落地
- 需要并行拆 lane 的任务
- 需要把设计一致性、HIG、无障碍、工程验证一起卡门的任务

#### 7. 技能仓库或本地 skill 生态本身需要治理

这不是业务需求场景，应该单独使用 `r0-skill-man`。

适用于：

- 清理废弃 skill
- 统一 skill frontmatter / 输出契约
- 收敛重复能力
- 做日常 skill 维护和坏例子沉淀

不建议在普通产品需求里顺手混用 `r0-skill-man`，避免把“交付需求”和“治理技能系统”搅在一起。

### 一个更实用的口径

可以把这些 skill 粗分成四层：

- 理解层：`r0-roadmap`、`r0-read`、`r0-question`
- 需求定义层：`r0-request`
- 执行层：`r0-work`、`r0-writer`、`r0-ios-agents`、`r0-diagram-guard`、`r0-write-lark`
- 收尾层：`r0-review`、`r0-submit`

默认建议是：

- 先理解，再定义，再执行，最后收尾。

除非任务非常小且上下文非常清楚，否则不要跳过前两层直接进入 `r0-work`。

## 建议先二次改造，再长期使用

建议 clone 这套仓库的人，把这批 `r0-*` skill 视为一个基础版本，再逐步改造成更适合自己的工作流。

一个比较自然的做法是：

- 把“改造这套 skill”本身当成一个需求。
- 让 Codex 这类 agent CLI 基于你的工作流、目录结构、语言习惯和提交流程去协助改造。
- 跑几轮真实任务后，再继续收敛触发词、输出格式、本地记录规则和脚本。

这样通常会比手工一点点重写更省力，也更容易沉淀出真正适合你自己的 skill 体系。

## 快速开始（从 clone 到可用）

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

### 2. 一键安装软链接（推荐）

```bash
./scripts/sync_skill_links.sh
```

说明：
- 该脚本会同时同步到 `~/.codex/skills` 和 `~/.claude/skills`。
- 如果目标位置已有同名目录/文件，会先自动备份再创建软链接。
- 脚本默认会校验“当前仓库是否像完整 skill 根目录”；如果目标目录里已有更多 `r0-*` 技能，而当前仓库只包含部分目录，会直接阻断，避免把已有链接切到错误来源。
- 如需先拉取仓库最新内容再同步，使用：

```bash
./scripts/sync_skill_links.sh --pull
```

如果你明确只想同步当前仓库里这部分技能，可显式添加：

```bash
./scripts/sync_skill_links.sh --allow-partial
```

### 3. 验证安装

```bash
./scripts/check_skill_links.sh
ls -l ~/.codex/skills | rg 'r0-'
ls -l ~/.claude/skills | rg 'r0-'
```

如果 `check_skill_links.sh` 报来源不完整或存在失效软链接，先修复 skill 根目录，再决定是否执行同步。

### 4. 手动方式（可选，脚本不可用时）

```bash
mkdir -p ~/.codex/skills ~/.claude/skills
for d in r0-*; do
  ln -sfn "$(pwd)/$d" ~/.codex/skills/"$d"
  ln -sfn "$(pwd)/$d" ~/.claude/skills/"$d"
done
```

注意：手动方式同样只应在“完整 skill 根目录”中执行；如果当前只是一个临时 worktree、镜像或裁剪仓库，不要直接批量重建链接。

如果你已经打开了 Codex 或 Claude Code，会话中看不到新技能时，重开一次会话即可。

### 5. 在 Codex 中使用

1. 进入你的目标项目目录后启动 Codex。
2. 对 `r0-work`、`r0-request`、`r0-roadmap`、`r0-read`、`r0-writer` 这类主 skill，建议在提示词开头显式写 skill 名，例如 `$r0-work`、`$r0-request`。
3. `r0-review`、`r0-submit` 通常更简单，直接写 `$r0-review` 或 `$r0-submit` 就可以，不一定需要再补额外提示词。

示例提示词：
- `$r0-request 把这个需求整理成可执行的 DSL，并写入 ./r0/request/。`
- `$r0-work 完成这个需求，只改动 api 模块。`
- `$r0-roadmap 阅读这个仓库，输出架构、功能边界和主流程。`
- `$r0-writer 把我的资料整理成一篇公众号长文，并补齐 outline、style 和 draft。`
- `$r0-review`
- `$r0-submit`

### 6. 在 Claude Code 中使用

1. 进入你的目标项目目录后启动 Claude Code。
2. Claude Code 侧按 slash command 理解，建议使用 `/r0-work`、`/r0-read`、`/r0-request` 这类形式。
3. `r0-review`、`r0-submit` 通常更简单，直接输入 `/r0-review` 或 `/r0-submit` 即可。

示例提示词：
- `/r0-request 把我的需求整理成结构化提示词 DSL。`
- `/r0-read 阅读这个仓库，输出架构与主流程。`
- `/r0-work 完成这个需求，范围限制在 api 和 service 层。`
- `/r0-writer 把这份采访纪要改写成适合公众号发布的长文草稿。`
- `/r0-review`
- `/r0-submit`

### 7. 更新这套技能（推荐）

当仓库有新提交时：

```bash
cd /path/to/r0-skills
./scripts/sync_skill_links.sh --pull
```

如果只是内容更新，软链接会自动指向最新内容；如果新增了新的 `r0-*` 目录，脚本也会自动补齐链接。

### 8. 同步所有 Git 远端

当前仓库可配置多个远端，例如 `origin`、`cggame`、`github`。提交完成后，如果需要把当前分支推送到所有远端，可执行：

```bash
./scripts/sync_all_remotes.sh
```

只同步指定远端：

```bash
./scripts/sync_all_remotes.sh --remote origin --remote github
```

指定分支同步：

```bash
./scripts/sync_all_remotes.sh --branch main
```

说明：
- 该脚本默认会先检查“当前 Git 实际追踪的 `r0-*` skills”与本地安装根中指向本仓库的软链范围是否一致。
- 若某个 `r0-*` 目录只存在于工作树、但尚未纳入 Git tracked scope，预检仍会把它视为 partial source 信号并阻断默认同步。
- 若检测到当前仓库只是 partial source，或本地仍有指向已删除 skill 目录的失效软链，会先阻断，避免把“push 成功”误判成“全部 r0 skills 已同步”。
- 如你明确只想同步当前仓库已追踪的这部分 skills，可显式添加：

```bash
./scripts/sync_all_remotes.sh --branch main --allow-partial-scope
```
