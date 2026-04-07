question: 2026-04-01 时点下，prompt、eval、自动化、MCP 与 skill governance 的最新官方实践，哪些应继续收敛进 r0-* skill 巡检？
sources:
  - https://developers.openai.com/api/docs/guides/prompt-caching
  - https://developers.openai.com/api/docs/guides/prompt-optimizer
  - https://developers.openai.com/api/docs/guides/evaluation-best-practices
  - https://developers.openai.com/api/docs/guides/graders
  - https://developers.openai.com/api/docs/guides/background
  - https://developers.openai.com/api/docs/guides/batch
  - https://developers.openai.com/api/docs/guides/flex-processing
  - https://www.anthropic.com/engineering/building-effective-agents
  - https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
  - https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  - https://modelcontextprotocol.io/specification/2025-06-18
signals:
  - OpenAI 仍把“稳定前缀 + 变化尾部”视为 prompt caching 的核心前提，因此 `shared/r0-core-contract.md` 继续适合作为固定前缀，而不是把同类规则散落到不同 skill 的正文深处。
  - OpenAI Prompt Optimizer、Graders 与 Evaluation Best Practices 继续强调 dataset-backed iteration、可复跑 grader 和 workflow-level eval；对本地 skill 治理的直接映射是：contract 漂移必须通过 checker/脚本证据暴露，而不是只靠人工扫文档。
  - OpenAI Background / Batch / Flex 继续说明长耗时或低实时任务应异步化；对当前自动化的启示不是引入更复杂的平台，而是保持 `dry-run -> checker -> apply -> sync` 这样的可复跑、非阻塞闭环。
  - Anthropic 仍强调 workflow-first、small deterministic agents、harness-driven long-running work；这继续支持“shared contract + bad cases + research notes + maintenance log”的轻量治理，而不是继续扩 skill 数量。
  - MCP 2025-06-18 规范把 prompts/resources/tools/roots/sampling/elicitation 与 consent/safety 显式化；对本地 skill ops 的可采纳信号是：同步和远端推送这类高副作用动作必须先验证 source completeness、tracked state 与 safety gate。
adopt:
  - 保持 `shared/r0-core-contract.md` 作为单一契约源，并要求 `auto_evolve` 与 `check_r0_skill_record_dirs.py` 共享同一组最低断言。
  - 把 `shared result contract / 共享结果契约` 纳入所有 `r0-*` skills 的 shared contract 首段，减少 checker 对自由文本措辞的歧义依赖。
  - 继续要求每轮演进留下 `bad-cases/`、`research/`、`skill-maintenance-YYYY-MM-DD.md` 三类交接物，作为 long-running harness 的最小证据面。
  - 对同步/推送类动作继续沿用“先校验、后执行”的 least-privilege 策略；当 Git HEAD 未追踪目标 skill 目录时，禁止把“push main”误判为“技能已同步”。
not_adopt:
  - 暂不把远程 eval 平台、webhook 编排或多 agent 调度硬塞进本地 skill 维护流；当前主要收益仍来自 contract 对齐与脚本门禁收敛。
  - 暂不把结果卡片规则升级成更重的模板系统；共享 contract 中的轻量 Markdown 卡片仍足够稳定。
  - 暂不自动执行三个远端 push；在当前仓库 HEAD 仅追踪 `r0-review`、`r0-submit`、`scripts/`、`shared/` 的前提下，直接 push 不能同步本轮多数 skill 变更，属于假成功风险。
