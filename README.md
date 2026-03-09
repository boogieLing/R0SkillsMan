# skills-man

本仓库用于维护一组 `r0-*` 本地技能，覆盖代码实现、代码阅读、审查、提交流程、图资产门禁、iOS 协同开发和 Lark 同步等场景。

## 技能清单与作用

| Skill | 作用 |
| --- | --- |
| `r0-diagram-guard` | 对文章目录中的流程图资产做质量门禁与自动修复，重点处理黑块、截断、占位图、坏引用等问题，并输出门禁报告。 |
| `r0-ios-agents` | 作为 iOS 任务总编排器，按依赖关系协调多技能并行执行（如 Figma 到 SwiftUI 的实现、动画、可访问性与质量门禁）。 |
| `r0-question` | 中文知识问答与思路分析助手，要求用分点结构输出，适合概念解释、方案梳理与问题拆解。 |
| `r0-read` | 只读型代码库阅读技能，用结构化流程理解项目架构、模块、数据流与关键控制流，并沉淀本地文档。 |
| `r0-review` | 系统化代码审查技能，围绕正确性、安全性、复杂度、可读性和可维护性输出可复核结论。 |
| `r0-skill-man` | 本地技能生态的日常维护技能，用于清理冗余、审计优化、提炼问题模式并生成维护日志。 |
| `r0-submit` | 开发收尾提交编排技能，先审查再分组提交，使用 `r0push` 推送，并在本地记录提交过程。 |
| `r0-work` | 面向工程交付的实施技能，强调严格流程、范围控制和多语言项目下的生产级代码实现。 |
| `r0-write-lark` | 将本地文章目录按自然语言指令同步到 Lark/飞书云文档，支持自动匹配文章、导入并回写元数据。 |

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
- 如需先拉取仓库最新内容再同步，使用：

```bash
./scripts/sync_skill_links.sh --pull
```

### 3. 验证安装

```bash
ls -l ~/.codex/skills | rg 'r0-'
ls -l ~/.claude/skills | rg 'r0-'
```

### 4. 手动方式（可选，脚本不可用时）

```bash
mkdir -p ~/.codex/skills ~/.claude/skills
for d in r0-*; do
  ln -sfn "$(pwd)/$d" ~/.codex/skills/"$d"
  ln -sfn "$(pwd)/$d" ~/.claude/skills/"$d"
done
```

如果你已经打开了 Codex 或 Claude Code，会话中看不到新技能时，重开一次会话即可。

### 5. 在 Codex 中使用

1. 进入你的目标项目目录后启动 Codex。
2. 在提示词中明确点名技能名。

示例提示词：
- `使用 r0-review 对当前改动做一次 quick 审查，并给出高风险问题。`
- `使用 r0-work 完成这个需求，只改动 api 模块。`

### 6. 在 Claude Code 中使用

1. 进入你的目标项目目录后启动 Claude Code。
2. 在提示词中明确点名技能名。

示例提示词：
- `请使用 r0-read 阅读这个仓库，输出架构与主流程。`
- `请使用 r0-submit 进行收尾提交流程，不要改业务代码。`

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
