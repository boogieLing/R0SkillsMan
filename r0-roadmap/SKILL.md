---
name: r0-roadmap
description: Read the architecture of a specified directory, analyze its functional responsibilities and feature flows, and produce a documented roadmap under the target project's `./r0/roadmap/`. Use when Codex needs to understand a codebase or subdirectory, summarize modules plus features into a roadmap, or sync a roadmap summary into the project's global `AGENTS.md` if one exists.
---

# R0 Roadmap

## Shared Contract

- 执行前必须加载 `../shared/r0-core-contract.md`。
- 结果输出必须遵循 shared result contract / 共享结果契约：先给统一的 `首屏摘要卡片`，再给结构化正文与 `自动进化`。
- 本技能在目标项目中的本地记录目录固定为 `./r0/roadmap/`。
- 每次生成 roadmap 后，必须把结果文档写入目标目录下的 `./r0/roadmap/`。
- 若目标项目存在全局 `AGENTS.md`，必须尝试把 roadmap 摘要同步进 `AGENTS.md` 的受管区块。
- `.gitignore` 统一规则为 `r0/`；若本地记录被误加入暂存区，执行 `git restore --staged -- r0/ 'r0-*'`。

## Inputs

执行前明确以下输入：

1. `target_dir`
   - 用户指定要阅读和总结的目录。
   - 若用户给的是仓库根，则对整个项目输出 roadmap。
   - 若用户给的是子目录，则聚焦该子目录及其直接依赖关系。
2. `analysis_goal`
   - 默认目标：读架构、分析功能、生成 roadmap、文档化。
   - 若用户额外要求“按模块 / 按阶段 / 按优先级 / 按风险”组织，必须显式带入 roadmap。
3. `scope_boundary`
   - 明确是“只读分析+文档化”，不默认修改业务代码。
   - 允许修改：`./r0/roadmap/*` 与 `AGENTS.md` 中由本技能管理的区块。

## Output Artifacts

默认输出文件：

- `./r0/roadmap/roadmap-YYYYMMDD-HHMMSS.md`

建议内容结构：

1. 项目 / 目录概览
2. 架构结构总览
3. 功能域拆分
4. 模块与职责映射
5. 关键流程 / 关键链路
6. roadmap 建议
7. 风险 / 未决问题
8. 下一步建议

若检测到全局 `AGENTS.md`，还要把一份简短 roadmap 摘要写入受管区块：

- 开始标记：`<!-- r0-roadmap:start -->`
- 结束标记：`<!-- r0-roadmap:end -->`

## Workflow

### Step 1: Scope Lock

- 解析 `target_dir` 并转成绝对路径。
- 确认目录存在；不存在则立即阻断。
- 判断分析层级：
  - 单模块目录
  - 子系统目录
  - 仓库根目录
- 明确哪些内容纳入分析：
  - 目录结构
  - 核心入口
  - 关键配置
  - 模块依赖
  - 功能链路
- 明确哪些内容不纳入：
  - 无关生成产物
  - 巨型二进制文件
  - 无关 vendor / cache / build 输出

### Step 2: Architecture Reading

- 优先使用快速命令理解目录结构：
  - `rg --files`
  - `find`
  - `tree`（若环境存在）
- 重点读取：
  - 入口文件
  - 路由 / handler / controller / service / model
  - 核心配置文件
  - 构建脚本 / package 管理文件
  - 现有 `README.md`、`AGENTS.md`、设计文档
- 若目录很大，先抽取：
  - 顶层目录
  - 每层关键文件
  - 明显入口点
  - 关键依赖边界

### Step 3: Feature Analysis

- 从代码与文档反推功能域，而不是只列目录树。
- 至少输出这些分析维度：
  - 每个模块负责什么功能
  - 哪些模块共同形成一个业务能力
  - 哪些目录是基础设施，哪些是业务层
  - 哪些部分耦合度高、可演进性差或上下游不清晰
- 若证据不足，必须显式写 `待确认`，不能把推断写成事实。

### Step 4: Roadmap Synthesis

- 把“目录架构”与“功能能力”合并成一个可行动 roadmap，而不是两份平行清单。
- roadmap 默认应包含：
  - 当前结构现状
  - 功能能力地图
  - 优先整理项 / 演进项
  - 推荐分阶段动作
- 当用户没有指定排序方式时，默认按：
  - 基础能力
  - 核心业务能力
  - 支撑能力 / 工具链
  - 演进建议

### Step 5: Documentation Write

- 在目标目录下创建：
  - `./r0/roadmap/`
- 文档文件名使用：
  - `roadmap-YYYYMMDD-HHMMSS.md`
- 写入前先保证：
  - 历史 `r0-*` 本地记录目录按共享契约迁移
  - `.gitignore` 已覆盖 `r0/` 与 `r0-*/`
- 写完后，若 `r0/` 被误暂存，执行：
  - `git restore --staged -- r0/ 'r0-*'`

### Step 6: Global AGENTS Sync

- 自动检查全局 `AGENTS.md`：
  - 优先在 `target_dir` 向上逐级查找，直到仓库根。
  - 只处理找到的第一个“全局 AGENTS.md”。
- 若存在 `AGENTS.md`：
  - 调用 `scripts/sync_roadmap_to_agents.py`
  - 将 roadmap 摘要写入 `r0-roadmap` 受管区块
  - 不覆盖该区块外的人工内容
- 若不存在：
  - 明确报告“未发现全局 AGENTS.md”，但这不阻断 roadmap 生成

## AGENTS Sync Script

使用：

```bash
python3 <skill-dir>/scripts/sync_roadmap_to_agents.py --target-dir <target_dir> --roadmap-file <roadmap_file>
```

脚本职责：

- 自 `target_dir` 向上定位全局 `AGENTS.md`
- 生成精简 roadmap 摘要
- 以受管区块形式写入或更新 `AGENTS.md`
- 不修改受管区块外的内容

## Quality Bar

- 不能只输出目录树。
- 不能只输出功能列表。
- 必须把“目录架构”和“功能职责”结合成 roadmap。
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
- 是否发现并更新 `AGENTS.md`
- 关键架构结论
- 关键功能结论
- 仍待确认的问题
