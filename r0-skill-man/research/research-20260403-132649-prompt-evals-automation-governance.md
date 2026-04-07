question: 截至 2026-04-03，围绕 `r0-*` skills 的提示词、评测、自动化与技能治理，哪些一手实践仍然稳定，且值得直接收敛到本地巡检与同步流程？
sources:
  - https://developers.openai.com/codex/skills
  - https://developers.openai.com/api/docs/guides/prompt-optimizer
  - https://platform.openai.com/docs/guides/evaluation-best-practices
  - https://platform.openai.com/docs/guides/background
  - https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  - https://modelcontextprotocol.io/specification/2025-06-18
signals:
  - OpenAI 继续把 skills 定义为可复用的指令与工作流封装，适合沉淀稳定前缀、工具门禁和执行步骤，而不是每轮对话手写长 prompt。
  - OpenAI prompt optimizer 与 eval best practices 仍强调“先固定任务目标，再围绕 eval 结果迭代 prompt”，说明 skill 治理不应只看主观顺手与否，而要围绕坏例子和可重复检查项收敛。
  - OpenAI background guide 继续支持长任务放到可恢复、可轮询、状态外显的执行模式中；这与周期性 skill 巡检、批量同步和守护脚本的形态一致。
  - Anthropic 的 long-running harness 继续强调 initializer / working notes / summarizer 之类的阶段化交接，支持把自动化拆成“发现问题 -> 写记录 -> 执行校验 -> 再决定是否 apply”的短闭环。
  - MCP 2025-06-18 规范继续把 roots、tools、elicitation、consent 作为边界控制点，这支持“默认阻断 partial source/失效软链/不确定远端”的安全前置，而不是先推送后解释。
adopt:
  - 保持 shared contract + checker/script 的治理方式，把本地记录路径、结果卡片约束和同步安全门禁固化到脚本，而不是只留在 README 口头说明。
  - 持续把最近 bad cases 作为演进入口，再把收敛动作落成低风险 preflight，例如 scope gate、DNS/connectivity check、explicit override flag。
  - 对远端同步、软链同步、自动 apply 这类高风险动作保持 workflow-first：先做范围校验和环境校验，再决定是否执行。
  - 保留“显式 override 才继续”的设计，例如 `--allow-partial-scope`，避免自动化把 partial source 误判成全量技能源。
not_adopt:
  - 不把 broken links 自动清理成默认动作；当前缺少“这些旧 skill 是否已正式退役”的仓库级决策，自动 prune 风险仍偏高。
  - 不把 working tree 中存在但未纳入 Git tracked scope 的目录直接当作可发布 skill；发布范围应继续以 Git 追踪结果为准。
  - 不把“远端 push 成功”视为“本地 skill 根目录与所有安装根都已同步”；两者必须分别校验。
