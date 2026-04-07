question: 2026-03-28 时点下，prompt、eval、自动化与 skill governance 有哪些最新信号，适合继续收敛到 r0-* skills？
sources:
  - https://platform.openai.com/docs/guides/prompt-caching
  - https://platform.openai.com/docs/guides/evaluation-best-practices
  - https://platform.openai.com/docs/guides/graders/
  - https://platform.openai.com/docs/guides/background
  - https://www.anthropic.com/engineering/building-effective-agents?via=aitoolhunt
  - https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
  - https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents?lid=1f0n56CPItf3Nm9NR
  - https://docs.langchain.com/langsmith/manage-prompts
  - https://docs.langchain.com/langsmith/manage-prompts-programmatically
  - https://docs.langchain.com/langsmith/use-webhooks
signals:
  - Prompt side: OpenAI 继续强调“稳定前缀 + 变化尾部”以提高 prompt cache 命中率；LangSmith 也把 prompt commit/tag/caching 做成一等能力，说明 prompt 资产应被版本化而不是只靠自然语言复制。
  - Eval side: OpenAI 强调 eval-driven development、持续评测、日志反哺数据集；Anthropic 2026-01 的 agent eval 文章进一步说明，agent 评测必须覆盖工具调用、状态转移、handoff 与多轮轨迹，而不只是最终答案。
  - Automation side: OpenAI 的 background 模式继续把“长耗时任务异步化”作为标准能力；LangSmith 的 prompt/rule webhooks 则说明，prompt 或 run 变更后自动触发下游校验已经是成熟模式。
  - Governance side: Anthropic 仍强调先选 workflow 再选 agent，复杂度必须由评测证明；2025-11 的 long-running harness 文章则把“显式留痕、跨 session 交接物”提升为长链路 agent 的核心基础设施。
  - Skill ops side: 对本地 `r0-*` 技能而言，shared contract 仍应保持中心化，具体技能只做最小必要引用；真正的治理抓手应是轻量 checker、坏例子沉淀和可复跑同步校验。
adopt:
  - 继续把 `shared/r0-core-contract.md` 作为单一约束源，并要求各技能文档显式引用。
  - 对 skill/prompt 的结构收敛，优先做“低风险元数据与 contract 修补”，避免自动化直接重写大段行为指令。
  - 后续可考虑为 `r0-skill-man` 增加一个轻量 drift checker，专门校验：shared contract 引用、本地记录路径、`git restore --staged -- r0/ 'r0-*'`、结果卡片关键词是否齐备。
  - 若以后开始版本化 prompt/skill 文本，可借鉴 LangSmith 的 tag/webhook 思路，为技能演进引入“变更触发巡检”的自动化门禁。
  - 长链路自动化继续要求留下本地维护日志、bad case、research note，避免跨 session 丢上下文。
not_adopt:
  - 暂不把完整的 LangSmith/OpenAI 平台能力强塞进本地 skill 体系；当前主要问题仍是本地 contract 漂移与脚本鲁棒性，不是平台缺能力。
  - 暂不把 agent 化复杂度继续上提；Anthropic 的结论仍成立，未被评测证明前不应把简单 workflow 重写成多 agent。
  - 暂不自动重建全局软链接；当前环境对 `~/.codex/skills` 写入仍有权限约束，保持“先校验、再在可信根目录同步”的策略更稳妥。
