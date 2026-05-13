---
name: r0-roadmap
description: Read and understand a target project or directory, analyze architecture with AST-assisted evidence, map modules and feature flows, and produce a documented roadmap under the target project's `./r0/roadmap/`. Use when Codex needs systematic codebase reading, architecture analysis, functional responsibility mapping, roadmap planning, or syncing a roadmap summary into the project's global `AGENTS.md` if one exists.
---

# R0 Roadmap

`r0-roadmap` absorbs the former `r0-read` responsibility. It is now the single skill for:

- read-only codebase understanding
- entry point and control-flow analysis
- architecture and module responsibility mapping
- AST-assisted project structure analysis
- roadmap documentation and optional `AGENTS.md` summary sync

## Shared Contract

- 执行前必须加载 `../shared/r0-core-contract.md`。
- 结果输出必须遵循 shared result contract / 共享结果契约：先给统一的 `首屏摘要卡片`，再给结构化正文与 `自动进化`。
- 本技能在目标项目中的本地记录目录固定为 `./r0/roadmap/`。
- 每次执行必须把 roadmap 文档写入目标目录下的 `./r0/roadmap/`。
- `r0-roadmap` 不再写入旧 read 记录目录；阅读摘要必须并入 roadmap 文档。
- 若目标项目存在全局 `AGENTS.md`，必须尝试把 roadmap 摘要同步进 `AGENTS.md` 的受管区块。
- `.gitignore` 统一规则为 `r0/` 与兼容规则 `r0-*/`；若本地记录被误加入暂存区，执行 `git restore --staged -- r0/ 'r0-*'`。

## Inputs

执行前明确以下输入：

1. `target_dir`
   - 用户指定要阅读、分析和总结的目录。
   - 若用户给的是仓库根，则对整个项目输出 roadmap。
   - 若用户给的是子目录，则聚焦该子目录及其直接依赖关系。
2. `analysis_goal`
   - 默认目标：系统化读代码、分析架构、反推功能、生成 roadmap、文档化。
   - 若用户额外要求“按模块 / 按阶段 / 按优先级 / 按风险”组织，必须显式带入 roadmap。
3. `scope_boundary`
   - 明确是“只读分析 + 本地文档化”，不默认修改业务代码。
   - 允许修改：`./r0/roadmap/*` 与 `AGENTS.md` 中由本技能管理的区块。

## Output Artifacts

默认输出文件：

- `./r0/roadmap/roadmap-YYYYMMDD-HHMMSS.md`
- `./r0/roadmap/ast-architecture-YYYYMMDD-HHMMSS.md`
- `./r0/roadmap/ast-architecture-YYYYMMDD-HHMMSS.json`

Roadmap 文档必须包含：

1. 项目 / 目录概览
2. 语言、技术栈与项目类型判断
3. 入口点与控制流
4. 架构结构总览
5. 目录、模块与职责映射
6. 核心数据结构 / 模型 / 抽象
7. 关键功能域与功能链路
8. AST 辅助证据摘要
9. roadmap 建议
10. 风险 / 未决问题
11. 下一步建议

若检测到全局 `AGENTS.md`，还要把一份简短 roadmap 摘要写入受管区块：

- 开始标记：`<!-- r0-roadmap:start -->`
- 结束标记：`<!-- r0-roadmap:end -->`

## Mandatory Workflow

### Step 1: Scope Lock

- 解析 `target_dir` 并转成绝对路径。
- 确认目录存在；不存在则立即阻断。
- 判断分析层级：
  - 单模块目录
  - 子系统目录
  - 仓库根目录
- 明确纳入分析的内容：
  - 目录结构
  - 入口文件
  - 路由 / handler / controller / service / model
  - 核心配置
  - 模块依赖
  - 功能链路
- 明确排除内容：
  - 生成产物
  - 巨型二进制文件
  - vendor / cache / build 输出
  - 与目标目录无关的旁支代码

### Step 2: Stack Identification

必须先判断：

- 主要编程语言
- 主要技术栈和框架
- 项目类型：
  - Frontend
  - Backend
  - Full-stack
  - Library / SDK / Tooling
  - Mobile / Desktop / CLI

该判断决定后续阅读视角。

### Step 3: AST-Assisted Architecture Scan

在人工阅读前，优先运行本技能脚本生成结构证据：

```bash
python3 <skill-dir>/scripts/analyze_project_ast.py --target-dir <target_dir>
```

大仓或需要完整证据时可使用：

```bash
python3 <skill-dir>/scripts/analyze_project_ast.py --target-dir <target_dir> --workers 0 --full-files
```

脚本输出：

- `ast-architecture-YYYYMMDD-HHMMSS.md`
- `ast-architecture-YYYYMMDD-HHMMSS.json`

脚本能力：

- 对 Python 文件使用标准库 `ast` 解析真实语法树。
- 对 JS / TS / Swift / Go / Java / Kotlin / Rust 使用轻量结构扫描提取 imports、symbols、入口候选和分层信号。
- 将 import 解析为文件级依赖图，区分 resolved / unresolved internal / external。
- 使用并查集聚合强相关文件，输出架构簇与功能域候选。
- 使用 Tarjan SCC 识别循环依赖和强耦合分量。
- 将 SCC 压缩为 DAG 后做分层，辅助判断入口层、编排层和依赖层方向。
- 输出 fan-in、fan-out、bridge score 等中心性信号，识别核心抽象、编排文件和跨域桥接点。
- 使用目录前缀聚合输出目录热区，辅助判断模块边界和维护重点。
- 使用 `os.walk` 剪枝、预计算行号 offset、`heapq.nlargest` 和可选并行 workers 优化大仓性能。

使用约束：

- AST 报告是证据输入，不是最终结论。
- `structural-scan` 只能作为辅助信号，必须通过关键源码阅读确认。
- 若脚本失败，不阻断 roadmap，但必须在最终结果中说明失败原因并继续人工阅读。

### Step 4: Systematic Reading

按以下顺序读代码，不能只看目录树：

1. Entry Point Identification
   - Identify how the project starts.
   - Explain how control first enters the system.
2. High-Level Architecture Overview
   - Identify major layers or modules.
   - Explain responsibilities of each layer.
3. Directory & Module Structure
   - Explain purpose of each major directory.
   - Distinguish core modules from auxiliary modules.
4. Core Data Structures & Models
   - Identify key data structures, models, entities, or central abstractions.
   - Explain how data flows through the system.
5. Key Control Flow
   - Trace main execution paths.
   - Explain how requests, tasks, events, or commands propagate.
6. Critical Logic & Non-obvious Design
   - Identify logic that is central, complex, performance-sensitive, or easy to misunderstand.
   - Explain why it is designed that way only when code evidence supports it.
7. Configuration & Extension Points
   - Identify configuration files and runtime options.
   - Identify plugin, extension, hook, or adapter mechanisms.

必须区分：

- `代码明确事实`
- `基于证据的推断`
- `待确认`

### Step 5: Feature Analysis

- 从代码与文档反推功能域，而不是只列目录树。
- 至少输出这些分析维度：
  - 每个模块负责什么功能
  - 哪些模块共同形成一个业务能力
  - 哪些目录是基础设施，哪些是业务层
  - 哪些部分耦合度高、可演进性差或上下游不清晰
- 若证据不足，必须显式写 `待确认`，不能把推断写成事实。

### Step 6: Roadmap Synthesis

- 把“读代码结论”“AST 结构信号”“目录架构”“功能能力”合并成一个可行动 roadmap。
- Roadmap 默认包含：
  - 当前结构现状
  - 功能能力地图
  - 优先整理项 / 演进项
  - 推荐分阶段动作
- 当用户没有指定排序方式时，默认按：
  - 基础能力
  - 核心业务能力
  - 支撑能力 / 工具链
  - 演进建议

### Step 7: Documentation Write

在目标目录下创建：

- `./r0/roadmap/`

文档文件名使用：

- `roadmap-YYYYMMDD-HHMMSS.md`

写入前先保证：

- 历史 `r0-*` 本地记录目录按共享契约迁移。
- `.gitignore` 已覆盖 `r0/` 与 `r0-*/`。

必要命令：

```bash
python3 /Users/r0/.codex/skills/r0-submit/scripts/migrate_r0_record_dirs.py --repo-root .
touch .gitignore
rg -n '^r0/$' .gitignore || printf '\nr0/\n' >> .gitignore
rg -n '^r0-\*/$' .gitignore || printf 'r0-*/\n' >> .gitignore
git restore --staged -- r0/ 'r0-*'
```

### Step 8: Global AGENTS Sync

- 自动检查全局 `AGENTS.md`：
  - 优先在 `target_dir` 向上逐级查找，直到仓库根。
  - 只处理找到的第一个“全局 AGENTS.md”。
- 若存在 `AGENTS.md`：
  - 调用 `scripts/sync_roadmap_to_agents.py`
  - 将 roadmap 摘要写入 `r0-roadmap` 受管区块
  - 不覆盖该区块外的人工内容
- 若不存在：
  - 明确报告“未发现全局 AGENTS.md”，但这不阻断 roadmap 生成。

使用：

```bash
python3 <skill-dir>/scripts/sync_roadmap_to_agents.py --target-dir <target_dir> --roadmap-file <roadmap_file>
```

## Quality Bar

- 不能只输出目录树。
- 不能只输出功能列表。
- 不能把 AST 报告当最终结论。
- 必须把“阅读证据、目录架构、功能职责、演进路线”合成一份 roadmap。
- 文档必须可扫读、可交接、可继续演化。
- 若某些模块职责或链路缺证据，必须显式标出 `待确认`。

## Final Response Contract

最终输出必须包含：

1. `首屏摘要卡片`
2. `执行摘要`
3. `关键产物`
4. `验证 / 证据`
5. `风险 / 下一步`
6. `自动进化`

结果中至少说明：

- 分析目标目录
- 输出 roadmap 文件路径
- 输出 AST 报告路径
- 是否发现并更新 `AGENTS.md`
- 关键架构结论
- 关键功能结论
- 仍待确认的问题
