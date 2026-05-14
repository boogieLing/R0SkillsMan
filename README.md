# r0-skills

这是一个本地 skill 仓库，主要给 Codex / Claude Code 用。

仓库里放的是一组按场景拆开的 `r0-*` skills，比如需求整理、代码实施、后端约束、代码审查、提交收尾、写作交付。除了 skill 本身，这里也放了共享契约、安装脚本、同步脚本和一些本地记录规范。

## 项目定位

- `r0-*` 目录是各个 skill 的源码目录。
- `shared/` 放跨 skill 复用的统一契约。
- `scripts/` 放安装、同步、初始化和校验脚本。
- 仓库根目录下的 `r0/` 放本地执行记录、坏例子、研究笔记和阶段产物。
- `shared/token-efficient-prompting.md` 是所有 skill 的基础开发逻辑：结构化输入、专家模式、输出预算、Delta 输出、No preamble、术语压缩和负约束优先。

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
| `r0-request` | 把自然语言需求整理成结构化执行 DSL，抽取目标、成功标准、范围、约束、任务 DAG、验证系统和交付格式；后端方案会融合 `r0-restrict` 的数据流、IO、依赖与 To-C 约束，并通过脚本保存与校验 `./r0/request/` 文档。 |
| `r0-restrict` | 后端方案约束与技术评审层，强制从数据流转、IO 操作、组件依赖三维推演，覆盖 DB/Redis/RPC/MQ/定时任务/分布式锁/高并发、防刷、兼容性、降级和可观测性，可嵌入 `r0-request`、`r0-work`、`r0-review`。 |
| `r0-work` | 长时间工程实施 skill，负责范围锁定、git baseline、分阶段实现、编译验证、失败控制与自动修复闭环；内置语言参考约束（Go/Python/Rust/Swift）和方法注释、逻辑注释、复杂度检查脚本，用于把实现质量门禁前置。 |
| `r0-review` | 结构化代码审查 skill，面向变更代码、脚本和交付产物做 bug、回归、安全、复杂度、可维护性和测试缺口检查；强调 findings-first 输出，并把重要审查记录沉淀到 `./r0/review/`。 |
| `r0-submit` | 提交与推送安全收尾 skill，负责提交范围核查、review-before-push、提交记录、远端分支快照和安全调用 `r0push`；`r0push` 会选择推送 remote、识别目标分支、生成 source branch，并给出 GitHub PR / GitLab MR 路由。 |

### 代码阅读与架构理解

| Skill | 作用 |
| --- | --- |
| `r0-roadmap` | 项目/目录架构阅读与 roadmap 生成 skill，融合原 `r0-read` 的系统化读代码流程；使用 AST、结构扫描、依赖图、并查集、Tarjan SCC、DAG 分层、中心性和目录热区分析入口、模块、依赖、职责与功能流，并输出 `./r0/roadmap/` 文档和可选 `AGENTS.md` 摘要。 |
| `r0-question` | 低 token 的中文探索式问答、联网真源检索、问题挖掘、脑暴、思路分析与方案扩展 skill，适合把模糊问题拆成 `Task / Context / Constraints / Output`、前提、变量、真实外部信号、方向选项、取舍判断和下一步行动；会检索官方资料、GitHub、Reddit、论坛等来源，不默认改代码。 |

### 运营与专项场景

| Skill | 作用 |
| --- | --- |
| `r0-skill-man` | 本地 skill 生态治理与日常维护 skill，用于清理废弃技能、巡检 shared contract、本地记录路径、摘要卡片约束和同步漂移；提供 `check_r0_shared_contract.py`、`auto_evolve_r0_skills.py`、`sync_r0_skills.py` 等治理脚本，并沉淀 bad case / maintenance 证据。 |
| `r0-tech-graph` | 技术架构图生成 skill，面向系统架构、流程架构、数据流、Agent 架构、部署图和拓扑图；默认产出浅色、自包含 HTML，配套 SVG 模板生成、箭头吸附、布局校验、HTML 包装、inline SVG 提取和可选 PNG 导出。 |
| `r0-writer` | 项目化长文写作 skill，面向公众号、技术分析、教程、产品稿和行业评论，把 notes、brief、链接、PDF、转录稿或粗稿整理为 `outline.md`、`style.md`、`draft.md`、`notes.md` 和发布级 Markdown。 |

### 仓库入口

- `shared/r0-core-contract.md` 是当前 skill 体系的共享契约入口
- `shared/token-efficient-prompting.md` 是所有 `r0-*` skill 的 Token-Efficient Prompting 基础开发逻辑
- `scripts/install_and_quick_start.sh` 是 `skills_man` 命令入口，负责自安装、安装、卸载和 quick start 编排
- `scripts/quick_start.sh` 负责命名初始化、skill 同步、链接校验与 `r0push` 固定
- `scripts/uninstall.sh` 负责清理误安装留下的 skill 软链、固定 push 工具和仓库目录
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
git clone https://github.com/boogieLing/R0SkillsMan r0-skills
cd r0-skills
```

### 2. 一键配置安装（推荐）

如果你希望直接下载并执行安装器，让它先注册为本地命令，再自动完成安装，直接运行：

```bash
curl -fsSL "https://f.shine-shy.com/skills_man.sh" | bash -s --
```

默认行为：

- 先安装命令工具到 `~/.local/bin/skills_man`
- 默认先从远端 `github` 拉取；如果 GitHub SSH 无权限或失败，会立即尝试 `origin`、`cggame`
- 默认分支 `main`
- 默认安装到 `~/.local/share/r0-skills`
- 如果直接从本地 skill 仓库执行 `scripts/install_and_quick_start.sh`，默认复用当前仓库，兼容旧版直接执行方式
- 如果检测到 Codex / Claude skill 软链已经指向旧安装仓库，默认反推出并复用该仓库
- 本地没有仓库时先 clone
- 安装目录已有 skill 仓库时默认更新；可显式跳过或覆盖
- clone / fetch 会按 `github -> origin -> cggame` 做远端回退，并输出实际选中的 `selected_remote`
- 拉取成功后自动继续执行仓库内的 `scripts/quick_start.sh`
- 如果旧安装仓库存在未提交改动，脚本会在 quick start 前停止，并输出 `git status`、`git stash`、`--allow-dirty` 处理指引

常用示例：

```bash
curl -fsSL "https://f.shine-shy.com/skills_man.sh" | bash -s --
curl -fsSL "https://f.shine-shy.com/skills_man.sh" | bash -s -- --name lyn
curl -fsSL "https://f.shine-shy.com/skills_man.sh" | bash -s -- --remote cggame --branch main --allow-dirty
skills_man install --overwrite
skills_man install --update-existing
skills_man install --skip-existing
skills_man uninstall
./scripts/install_and_quick_start.sh --dry-run
```

当前仓库已配置的三个远端是：

- `github`
- `origin`
- `cggame`

推荐顺序：

1. 首次安装时直接通过 `https://f.shine-shy.com/skills_man.sh` 下载并运行
2. 后续安装 / 更新 / 卸载优先使用 `skills_man`
3. 旧版已经直接执行过仓库内 `scripts/install_and_quick_start.sh` 的用户，可以继续直接执行；脚本会优先复用旧仓库
4. 需要切换自定义前缀时，加 `--name <your-prefix>`
5. 完成后优先使用 `$HOME/.local/bin/<prefix>push` 作为固定提交入口

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
- 输出 `source_skill_count`，用于确认当前仓库中的 `<prefix>-*` skill 已进入快速启动链路

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
- 把当前前缀当成占位符，批量替换仓库内文本中的前缀标识
- 重命名 `r0-*` 目录、相关脚本文件名和 `shared/r0-core-contract.md`
- 连 `r0push`、`check_r0push_scope.py`、`printf '\nr0/\n'` 这类 skill 内部复合命名和转义字符串也会一起替换成新前缀
- 把硬编码的 `/Users/r0/...` 路径收敛为 `$HOME/...`，避免克隆到别的机器后仍残留作者本地路径
- 实际执行后会扫描残留占位符；若源码区仍存在未替换的 `r0` / `R0` 前缀，会直接失败并列出文件位置
- 本地执行记录目录（例如根目录下的 `r0/`）不会参与命名重写，避免误改用户自己的历史记录

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

### 7. 卸载 / 清理误安装

如果你装错了前缀，或者只是想把这套本地 skill 完整移除，可以直接运行：

```bash
skills_man uninstall
```

默认行为：

- 默认卸载标准安装路径 `~/.local/share/r0-skills`
- 清理 `~/.codex/skills` 与 `~/.claude/skills` 中指向该仓库的 `<prefix>-*` 软链
- 清理 `~/.local/bin/<prefix>push`
- 最后删除安装仓库目录本身
- 最后清理 `~/.local/bin/skills_man`

常用示例：

```bash
skills_man uninstall --dry-run
skills_man uninstall --install-dir ~/work/r0-skills
./scripts/uninstall.sh --dry-run
./scripts/uninstall.sh --keep-repo
./scripts/uninstall.sh --repo-root ~/work/r0-skills
./scripts/uninstall.sh --repo-root ~/work/r0-skills --keep-repo
```

说明：

- 如果你当初用的是默认安装目录，直接运行 `skills_man uninstall` 即可
- 如果通过 `skills_man` 安装到了自定义目录，需要显式传 `skills_man uninstall --install-dir <path>`
- 如果直接调用 `./scripts/uninstall.sh`，对应参数是 `--repo-root <path>`
- `--keep-repo` 只清理本地安装入口，不删除仓库目录
- `--dry-run` 只输出计划删除的路径，不真正执行

### 8. 手动同步方式

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
- `$r0-tech-graph 画一个浅色 HTML 系统架构图，包含客户端、网关、服务层、数据库和消息队列。`

### Claude Code

Claude Code 侧通常用 slash command 风格：

- `/r0-roadmap 阅读这个目录，输出架构与功能边界。`
- `/r0-request 把我的需求整理成结构化提示词 DSL。`
- `/r0-restrict 约束当前后端技术方案，输出主要风险与门禁点。`
- `/r0-work 完成这个需求，范围限制在 api 和 service 层。`
- `/r0-review`
- `/r0-submit`
- `/r0-tech-graph 画一个浅色 HTML 系统架构图，包含 Agent、Tools、Memory 和外部 API。`

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
- 提示词与输出设计遵循 `shared/token-efficient-prompting.md`
- 默认使用 `Task / Context / Constraints / Output` 压缩问题
- 默认专家模式、No preamble、输出预算和 Delta 输出
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
./scripts/sync_all_remotes.sh --remote github --remote origin --remote cggame
./scripts/sync_all_remotes.sh --remote origin --remote github
./scripts/sync_all_remotes.sh --branch main
```

说明：

- 当前标准三端为 `github`、`origin`、`cggame`；不传 `--remote` 时脚本会同步到所有已配置远端
- 脚本会先检查当前仓库是否像一个“完整 skill 来源”
- detached HEAD 下若显式传 `--branch <name>`，upstream behind 检查会绑定到该目标分支，而不是当前 `HEAD`
- `--dry-run` 会逐个远端汇总 DNS / transport 预检结果，并输出对应的 `git push` 计划；若任一远端失败，会在汇总后统一阻断
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
