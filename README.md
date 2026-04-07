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
2. 在提示词中明确点名技能名。

示例提示词：
- `使用 r0-request 把这个需求整理成可执行的 DSL，并写入 ./r0/request/。`
- `使用 r0-review 对当前改动做一次 quick 审查，并给出高风险问题。`
- `使用 r0-work 完成这个需求，只改动 api 模块。`
- `使用 r0-writer 把我的资料整理成一篇公众号长文，并补齐 outline、style 和 draft。`

### 6. 在 Claude Code 中使用

1. 进入你的目标项目目录后启动 Claude Code。
2. 在提示词中明确点名技能名。

示例提示词：
- `请使用 r0-request 把我的需求整理成结构化提示词 DSL。`
- `请使用 r0-read 阅读这个仓库，输出架构与主流程。`
- `请使用 r0-submit 进行收尾提交流程，不要改业务代码。`
- `请使用 r0-writer 把这份采访纪要改写成适合公众号发布的长文草稿。`

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
