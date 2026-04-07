question: 2026-03-31 当前，提示词、评测、自动化与技能治理有哪些值得纳入 `r0-*` skills 巡检的最新一手实践？
sources:
  - https://platform.openai.com/docs/guides/prompt-engineering
  - https://platform.openai.com/docs/guides/background
  - https://platform.openai.com/docs/guides/evals
  - https://cookbook.openai.com/
  - https://www.anthropic.com/engineering/building-effective-agents
  - https://modelcontextprotocol.io/specification/2025-06-18
signals:
  - Prompting: 官方文档持续强调把指令、上下文、约束与输出 schema 显式拆开；对可复用任务应把提示词当版本化资产，而不是散落在流程描述里。
  - Evals: 官方 evals 指南与 Cookbook 都在强化“先定义可回归评测，再升级 prompt/model/tool chain”；评测应覆盖成功率、失败样本与边界样本，而不是只看 happy path。
  - Automation: OpenAI background mode 指向长耗时任务应异步化、可轮询、可恢复；这与本地 maintenance automation 的“先留记录、再同步、最后汇报”流程一致。
  - Agent orchestration: Anthropic 官方实践强调优先用 workflow，只有在确有价值时再升级为 agent；因此 `r0-*` skill 治理应优先强化确定性脚本和契约，而非增加新 agent。
  - Tool governance: MCP 规范持续强调工具调用边界、显式参数与信任/安全约束；本地 skill contract 应继续把 shared contract、记录目录与结果卡片作为显式门禁，而不是隐含约定。
adopt:
  - 将 `r0-skill-man` 的巡检重点继续收敛为三类固定门禁：shared contract、本地记录路径、结果卡片约束。
  - 把“文档命令必须可直接执行”视为新的低成本治理项；命令漂移要写 bad case，不再只记口头备注。
  - 保持 `auto_evolve -> manual review -> sync dry-run/apply` 的顺序，符合官方对 eval-first 与 workflow-first 的推荐。
  - 对长流程自动化继续采用“本地记录 + memory + inbox item”三层产物，保证异步可恢复。
not_adopt:
  - 不引入额外的通用 orchestrator skill；当前问题主要是 contract 漂移，不是编排能力缺失。
  - 不把联网研究结论直接自动改写进所有 `r0-*` skills；仍保持人工审阅后按需收敛，避免高风险内容漂移。
