---
name: r0-request
description: 把自然语言需求转换为结构化提示词 DSL，并尽量贴合 MULTI-AGENT CODING ORCHESTRATION TEMPLATE V3-FINAL 模板。适用于“把需求整理成 prompt/DSL/系统提示词/多 agent 编排模板/执行控制器模板”等场景；输出后必须落盘到 ./r0/request/，并自动保证该目录不进入 Git。
---

# r0-request

## Shared Contract
- 执行前必须加载 `../shared/r0-core-contract.md`。
- 结果输出必须遵循 shared result contract / 共享结果契约：先给统一的 `首屏摘要卡片`，再给结构化正文与 `自动进化`。
- 本技能的本地记录目录固定为 `./r0/request/`。
- 每次执行结束后，除 DSL 正文外，还必须补充一次结果摘要或自动进化记录到 `./r0/request/`。

## R0-RESTRICT 兼容层（后端方案场景强制）
- 当需求涉及后端技术方案设计、接口设计、数据库、Redis、RPC、MQ、定时任务、分布式锁、To-C 高并发链路时，必须加载 `../r0-restrict/SKILL.md`。
- 采用渐进式披露：先只读取 `r0-restrict` 主技能；只有在确认属于后端方案约束或需要 To-C 细则时，才继续读取 [../r0-restrict/references/backend-scheme-guardrails.md](../r0-restrict/references/backend-scheme-guardrails.md)。
- `r0-restrict` 产出的约束只能嵌入现有模板字段，不允许新增模板章节；优先落入：`NFRS`、`Data Flow Rules`、`Known Issues`、`Constraint System`、`Validation System`、`Success Criteria`、`DO_NOT_LIST`。
- 后端方案 DSL 至少要显式编码：数据流主链、禁止循环 IO、批量读写策略、扫库/扫缓存边界、缓存 TTL / 热点 Key 策略、幂等性、重试与超时、版本兼容、可观测性；To-C 场景再补限流/降级/熔断、防刷与 RT 约束。
- 若输入信息不足以判断上述约束，只能写 `ASSUMPTION:` / `待确认`，不得伪造容量、QPS、RT 或存储选型。

## 核心职责
- 将用户的自然语言目标压缩成可执行的提示词 DSL，而不是普通方案描述。
- 优先复用模板骨架，保留 `0` 到 `14` 的章节顺序与约束语义。
- 对缺失信息只做最小必要假设；不允许擅自扩需求。
- 在给出 DSL 后，必须写入本地文档目录 `./r0/request/`。

## 能力说明
- `r0-request` 的核心价值不是“写一段好看的 prompt”，而是把需求压缩成高结构、强约束、可执行的控制 DSL。
- 当 DSL 明确编码了目标、范围、阶段、任务 DAG、验证标准与失败处理时，很多模型会更容易进入“先规划、再执行、再校验”的控制器式工作风格。
- 对 Codex / Claude Code 这类 agent 环境，这种 DSL 往往能显著提升：
  - 计划式拆解
  - 范围约束
  - 验证优先
  - 状态更新与循环执行
- 这是一种“通过结构和约束影响模型行为”的能力，不是权限提升，也不是隐藏模式切换。
- 不允许把本技能描述成：
  - 可以伪装成 Codex 内部开发人员
  - 可以稳定触发未公开的内部模式 / 隐藏功能
  - 依赖所谓“魔法 token”或不可验证的黑箱咒语
- 允许的准确表述是：
  - `r0-request` 通过贴近 agent/controller 风格的 DSL 结构，提高模型进入规划模式、控制模式、验证模式的概率
  - `r0-request` 可以利用模型在后训练 / 指令对齐中学到的“结构化执行偏好”，但不能保证宿主一定暴露某个特定内置能力
  - 若宿主本身支持计划模式、结构化执行、阶段状态机或工具调用，`r0-request` 产出的 DSL 更容易与这些机制对齐

## 强制规则
- 先抽取：目标、成功标准、范围、约束、架构、阶段、任务 DAG、验证标准。
- 尽量保留模板中的英文章节名、控制语句和结构；内容可按用户语义填写。
- 缺失但必须填写的字段，使用 `TBD`、`待确认` 或 `ASSUMPTION:` 明示，不要伪造事实。
- 若用户需求明显不适合多代理编排，也仍然输出同一 DSL 框架，但把无关 agent / pipeline 最小化。
- 不输出泛泛的“建议”；直接输出可保存的 DSL 正文。
- 不允许把 `<<PLACEHOLDER>>` 原样留在最终结果里。
- 同一类缺失字段必须使用同一种处理方式；不要同一次输出里混用空白、猜测值、`TBD`、`ASSUMPTION:`。
- 默认先产出最小可执行 DSL；不要把“先追问一轮”当成默认流程。

## 执行流程
1. 读取用户原始需求，提炼下列信息：
- `PROJECT_NAME`
- `PROJECT_GOAL`
- `SUCCESS_CRITERIA`
- `IN_SCOPE_LIST`
- `OUT_OF_SCOPE_LIST`
- `NFRS`
- `PIPELINES`
- `TASK_DAG`
- `KNOWN_ISSUES`
2. 打开 [references/prompt-dsl-template.md](references/prompt-dsl-template.md)，按原章节顺序填充。
3. 对未提供的信息执行最小闭包补全：
- 只补维持模板可执行所必需的信息。
- 用一句话说明假设，不展开长篇解释。
4. 应用缺失信息策略：
- 以下字段允许直接写 `TBD`，且不要补猜测值：`PROJECT_NAME`、`PROJECT_GOAL`、`SUCCESS_CRITERIA`、`IN_SCOPE_LIST`、`OUT_OF_SCOPE_LIST`、`PHASE_2_NAME`、`PHASE_2_GOAL`、`PHASE_2_OUTPUT`、`PHASE_N_NAME`、`CUSTOM_AGENTS`。
- 以下字段缺失时必须给默认值，不允许留空，也不要写 `TBD`：`CURRENT_PHASE` 默认 `Phase 1 - Bootstrap`；`DONE_TASKS` 默认 `None`；`PENDING_TASKS` 默认 `Task 1 - Define minimal executable slice`；`ACTIVE_PIPELINES` 默认 `Pipeline A only`；`SYSTEM_STATUS` 默认 `Planning`；`PHASE_1_NAME` 默认 `Bootstrap`；`PHASE_1_GOAL` 默认 `Define the smallest executable implementation slice`；`PHASE_1_OUTPUT` 默认 `Minimal executable scaffold`；`PHASE_1_EXIT` 默认 `First end-to-end path is executable and validated`；`TASK_DAG` 默认 `Task 1 -> Task 2 -> Task 3`；`HARD_CONSTRAINTS` 默认 `No out-of-scope features`；`SOFT_CONSTRAINTS` 默认 `Readability preferred`；`DO_NOT_LIST` 默认 `Do not add features not explicitly requested`。
- 以下字段缺失时必须显式写 `ASSUMPTION:` 或 `待确认`，因为它们涉及执行边界，不能直接猜：`LATENCY_TARGET`、`NFRS`、`PIPELINE_A`、`PIPELINE_B`、`PIPELINE_N`、`DATA_FLOW_RULES`、`KNOWN_ISSUES`、`API_SPEC`、`DEPENDENCIES`、`FALLBACK_STRATEGY`、`USER_ACTION_1`、`USER_ACTION_2`、`USER_ACTION_3`。
- `CURRENT_PHASE`、`ACTIVE_PIPELINES`、`SYSTEM_STATUS`、`TASK_DAG` 即使信息不足也必须可执行，不能写成空泛套话，如“待后续规划”“按实际情况处理”。
5. 应用澄清门槛规则：
- 只有当缺失信息会直接改变 `PROJECT_GOAL`、`SUCCESS_CRITERIA`、`IN_SCOPE_LIST`、`OUT_OF_SCOPE_LIST`、`NFRS`、主架构选择或是否需要多 agent 编排时，才允许向用户追问。
- 可被 `TBD`、默认值、`ASSUMPTION:` 安全兜住的字段，不要追问。
- 一次最多追问 3 个问题，且每个问题都必须能改变 DSL 结构，而不是泛泛补背景。
- 若用户未回复，必须继续输出，不可卡住流程；直接按本技能的缺失信息策略生成 DSL。
- 追问应优先聚焦：范围边界、成功标准、核心非功能约束、是否真为多 agent 场景。
- 不要追问可后置的信息，如 `PHASE_2_*`、`PHASE_N_NAME`、非关键 `Custom Agents`、可默认的状态字段。
6. 参考 [references/examples.md](references/examples.md) 中最接近的范式，优先复用其中的信息压缩方式，而不是重新发明表达。
7. 输出结果时遵循以下顺序：
- `首屏摘要卡片`
- `需求摘要`
- `关键假设`
- `提示词 DSL`
- `文档路径`
- `校验结果`
- `自动进化`
8. 产出 DSL 后，立即调用脚本：

```bash
python3 r0-request/scripts/save_request_doc.py \
  --title "<标题>" \
  --source-request "<用户原始需求>"
```

将完整结果从标准输入写入文档。
9. 落盘后立刻校验：

```bash
python3 r0-request/scripts/validate_request_doc.py "<文档路径>"
```

只有校验通过，才可以把结果作为最终答案返回；若校验失败，必须修正 DSL 并重新保存、重新校验。

## 输出格式
- 自然语言输出必须使用中文。
- 最终回复必须先输出统一的 `首屏摘要卡片`，标题使用“随机颜表情 + 本次需求总结”。
- `提示词 DSL` 必须放入代码块，便于直接复制和复用。
- `文档路径` 必须给出脚本返回的实际文件路径。
- `校验结果` 必须给出校验脚本的结论。
- 如果脚本执行失败，必须明确报错，不可假装已落盘。
- 若本次需求暴露了提示词模板坏例子、信息缺口模式或外部最佳实践变化，必须补写 `自动进化`，并按需输出 `::automation-update{...}` 建议。

## 压缩模式
- 当用户需求不足 3 个明确功能点，或明显只是“整理思路/生成模板/快速起盘”时，必须进入压缩模式。
- 压缩模式下只保留最少必要结构：
- `Pipeline` 最多保留 `Pipeline A`，其余可写 `Not used in current phase`。
- `Agent` 只展开 `Agent 0` 加当前任务直接相关的 1 到 2 个 agent；无关 agent 可统一写 `Not used in current phase`。
- 非多代理场景允许 `Custom Agents` 直接写 `None`，不要为了凑模板强行发明角色。
- `Phase` 默认只展开 `Phase 1`；`Phase 2` 和 `Phase N` 可写 `TBD`。
- `TASK_DAG` 保持 2 到 4 个节点的最短可执行主链，不要平铺大量伪任务。
- 压缩模式的目标是“结构完整但内容克制”；禁止把模板章节扩写成无信息增量的空话。

## 落盘规范
- 输出目录固定为仓库根目录下的 `./r0/request/`。
- 文件名格式固定为：`request-YYYYMMDD-HHMMSS-<slug>.md`。
- `slug` 由标题生成；标题缺失时使用 `untitled`。
- 文档头部必须包含 frontmatter，至少包括：`title`、`created_at`、`source_request`、`template_version`。
- 文档内容直接保存最终回复中的结构化结果，避免再写第二份摘要。

## Git Hygiene
- 执行前先自动迁移历史目录：

```bash
python3 /Users/r0/.codex/skills/r0-submit/scripts/migrate_r0_record_dirs.py --repo-root .
```

- `./r0/request/` 仅用于本地需求文档，不允许进入版本控制。
- 执行前确认 `.gitignore` 已包含 `r0/`，并兼容历史目录规则 `r0-*/`。
- 若该目录被误加入暂存区，执行：

```bash
git restore --staged -- r0/ 'r0-*'
```

## 模板与边界
- 模板正文位于 [references/prompt-dsl-template.md](references/prompt-dsl-template.md)。
- 示例库位于 [references/examples.md](references/examples.md)。
- 不要改写模板的控制哲学：`PLAN → ACT → VERIFY → UPDATE STATE → LOOP`。
- 不要新增模板中不存在的大段方法论，除非用户明确要求扩展模板。
