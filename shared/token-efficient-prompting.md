# Token-Efficient Prompting

本项目所有 `r0-*` skill 的基础开发逻辑：通过提示词写法，让模型少读、少想、少写，同时尽量不降低结果质量。

## 核心原则

- 结构优先：用稳定字段降低理解成本。
- 专家模式：默认面向有上下文的专业受众，不解释基础概念。
- 输出受控：先约束长度、格式和范围，再生成内容。
- 增量优先：继续、优化、调整类任务只输出变化部分。
- 证据优先：需要事实输入时先检索真源，再做推断。
- 少样例：默认不用 few-shot；只有用户要求模板或示例时才给。

## 必用技巧

| 技术点 | 核心作用 | 项目内写法 |
| --- | --- | --- |
| 纯英文 / Telegraphic English | 用更短、更稳定的英文指令表达机器约束 | `Task: rewrite. Tone: formal. Output: final only.` |
| 结构化输入 | 减少模型理解成本 | `Task / Context / Constraints / Output` |
| 输出格式约束 | 控制输出 token | `Max 5 bullets. No intro. No summary.` |
| 专家模式 | 避免解释基础概念 | `Assume expert audience. No basics.` |
| Delta 输出 | 只输出变化部分 | `Output only changed sections.` |
| No preamble | 去掉开场白和废话 | `No preamble. Start with answer.` |
| 术语表 / 缩写表 | 压缩重复出现的长概念 | `SI = source input` |
| 上下文引用 | 避免重复贴全文 | `Use previous architecture A. Modify only risk section.` |
| 少样例 / 零样例 | 避免 few-shot 消耗 | `Follow this schema, no examples.` |
| 负约束 | 明确不要什么 | `Do not explain, expand, or restate input.` |
| 魔法 Prompt | 用短句触发压缩行为 | `Be concise. Output only actionable changes.` |

## Skill 开发约束

- `SKILL.md` 应优先写稳定流程、边界和输出契约，不写可被模型常识补齐的背景科普。
- 长规则放 `shared/` 或 `references/`，主 `SKILL.md` 只保留触发条件和必读入口。
- 工作流步骤使用短句和固定字段名；避免整段散文式说明。
- 输出结构必须可裁剪：简单任务允许压缩，复杂任务再展开。
- 任何“继续、优化、补充、调整”类指令默认采用 Delta 输出。
- 默认禁止 preamble、结尾总结、重复用户输入和无行动价值建议。
- 引入新能力时先判断能否用现有结构表达；不要为局部问题新增大段模板。

## 默认输出预算

- 简单答复：最多 5 条要点。
- 一般分析：最多 7 个小节，每节最多 5 条。
- 深度脑暴：最多 7 个方向，每个方向只写 `适用 / 价值 / 风险 / 验证`。
- 交付型结果：优先输出最终版；过程说明只在用户要求或风险需要时补充。

## 例外

- 法律、医疗、金融、安全等高风险领域可以突破预算，但必须解释为什么需要更多证据或限定条件。
- 用户明确要求教程、长文、报告、完整模板时，可以展开，但仍要保持结构化和可裁剪。
- 代码实现、审查、架构探索类任务可以保留必要证据链，但应避免重复粘贴无变化上下文。
