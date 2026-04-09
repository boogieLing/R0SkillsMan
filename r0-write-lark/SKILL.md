---
name: r0-write-lark
description: 将本地文章目录按自然语言指令同步到 Lark/飞书云文档。当前稳定能力是“同步前检查 + 素材清单 + 阻塞项归纳 + 可执行同步计划”；只有当前运行时明确具备 Lark 写入能力且目标文档信息充分时，才执行真实云端写入。
---

# r0-write-lark

## Shared Contract

- 执行前必须加载 `../shared/r0-core-contract.md`。
- 结果输出必须遵循 shared result contract / 共享结果契约：先给统一的 `首屏摘要卡片`，再给结构化正文与 `自动进化`。
- 本技能的本地记录目录固定为 `./r0/write-lark/`。
- 每次执行结束后，必须把同步前检查结果、素材映射、阻塞项或执行记录写入 `./r0/write-lark/`。
- `.gitignore` 统一规则为 `r0/`。
- 若本地记录被误加入暂存区，执行 `git restore --staged -- r0/ 'r0-*'`。

## Overview

把本地写作目录中的正文、标题、图片与流程图素材整理成可同步到 Lark/飞书的输入，并在真正写入前先做 readiness / scope / target 三类检查。

当前仓库中的 `r0-write-lark` 仍是占位型技能，但必须保持“不会误导触发、不会伪造云端成功、不会复用错误 skill 语义”这三条底线。

## Stable Scope

- `preflight`：检查文章目录、主 Markdown、图片/流程图素材、标题与同步目标信息是否齐全。
- `manifest`：输出本次准备同步的文件清单、目标文档、同步策略、阻塞项与人工确认点。
- `apply`：仅当当前运行时明确提供 Lark/飞书写入工具，且用户给出目标文档 / wiki / token / create-vs-update 决策后，才执行真实写入。

若缺少写入工具或目标文档信息，默认停在 `manifest`，而不是臆造“已同步”结果。

## Workflow

1. 识别目标文章目录，确认本次同步范围是 `outline`、`style`、`draft` 还是“整篇正文”。
2. 定位主 Markdown / 附件素材，区分“正文源文件”“仅本地参考文件”“需外链或上传的资产”。
3. 校验同步前条件：
   - 主体内容存在且非空
   - 若包含流程图，优先要求先过 `r0-diagram-guard`
   - 若目标是 update 现有文档，必须有明确的文档标识与替换范围
4. 生成同步清单与计划，列出：
   - source files
   - target doc / wiki / folder
   - create-vs-update 策略
   - blocker / risk / manual confirmation
5. 只有在工具能力与目标信息充分时，才执行真实 Lark 写入；否则输出可执行的下一步。

## Required Inputs

- 源文章目录或项目目录
- 期望同步范围：`outline | style | draft | full-article`
- 目标模式：`create-new-doc | update-existing-doc`
- 若执行真实写入：
  - 目标 doc / wiki / folder 标识
  - 是否允许覆盖现有内容
  - 当前运行时确实可用的 Lark/飞书工具

## Guardrails

- 没有真实工具回执时，不得声称“同步成功”。
- 不得把 `r0-diagram-guard` 的脚本、引用规则或输出口径继续冒充为本技能实现。
- 若目标文档不明确，默认阻断 `apply`，先输出 `manifest`。
- 若目录内素材尚不稳定，或图资产未过门禁，先要求修复源内容，再同步。
- 默认偏保守：优先 create new doc，或只替换显式指定区块，避免整篇静默覆盖。

## Current Repository State

- 当前仓库尚未内置稳定的 `r0-write-lark` 专用脚本。
- 如需真实写入，优先使用当前运行时可用的 Lark/飞书 connector 或 MCP 工具；若当前会话无对应工具，本技能只负责检查、归纳与计划。
- 这意味着本技能的“稳定承诺”是同步治理，不是伪装成已经完工的云同步器。

## Output Contract

执行结束必须提供：

1. readiness 状态：`ready | blocked | partial`
2. source scope：本次同步涉及哪些本地文件
3. target mode：新建还是更新，以及目标文档信息
4. blockers / risks / required confirmations
5. 本地记录路径：`./r0/write-lark/...`

最终回复必须先给统一的 `首屏摘要卡片`，标题格式为“随机颜表情 + 本次需求总结”，再给：
- `执行摘要`
- `关键产物`
- `验证 / 证据`
- `风险 / 下一步`
- `自动进化`

若发现新的同步漂移、目标映射误判、或高频重复操作，必须追加：
- `./r0/write-lark/bad-cases/...`
- `./r0/write-lark/research/...`
- 需要周期化时输出 `::automation-update{...}` 建议
