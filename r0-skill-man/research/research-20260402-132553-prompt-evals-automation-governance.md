question: 2026-04-02 时点下，prompt、eval、自动化、skills 与 MCP 治理有哪些最新一手实践值得继续收敛到 `r0-*` skills 巡检？
sources:
  - https://developers.openai.com/blog/skills-agents-sdk
  - https://platform.openai.com/docs/guides/prompt-caching
  - https://platform.openai.com/docs/guides/evals
  - https://platform.openai.com/docs/guides/background
  - https://www.anthropic.com/engineering/building-effective-agents
  - https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
  - https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  - https://modelcontextprotocol.io/specification/2025-06-18
signals:
  - OpenAI 在 2026-04-02 可见的一手材料里，仍把 `skills` 视为把高频、稳定、可复用工作流从主 prompt 中剥离出来的做法；这继续支持把 `r0-*` 的共享 contract 固定在 `shared/r0-core-contract.md`，而不是把规则散落进每个 skill 的自由文本。
  - OpenAI `prompt caching` 与 `evals` 仍强调稳定前缀、可复跑数据集和 grader 驱动迭代；对本地 skill 治理的直接映射是：contract 漂移必须优先通过 checker / dry-run / apply 证据暴露，而不是靠人工目测。
  - OpenAI `background` 仍强化长任务异步化与结果轮询思路；对当前自动化的启示仍是保持 `dry-run -> checker -> apply -> sync` 的保守状态机，而不是把巡检流程改成更复杂的串行大 prompt。
  - Anthropic 持续强调 workflow-first、deterministic harness、small agents；这继续支持 `bad-cases/`、`research/`、`skill-maintenance-YYYY-MM-DD.md` 作为长期演进的最小证据面。
  - MCP 规范继续把 prompts/resources/tools/roots/sampling/elicitation 与 consent/safety 显式建模；对本地 skill ops 的可采纳信号是：同步、本地链接刷新、远端 push 这些高副作用动作必须先经过 scope gate 和环境可达性检查。
  - 当前仓库被 Git 追踪的 `r0-*` 目录仍只有 `r0-review` 与 `r0-submit`；因此“push main 到三远端”默认只能同步少数 tracked 资产，不等于“全部 r0 skills 已发布”，这个风险仍未被脚本门禁收敛。
adopt:
  - 继续以 `shared/r0-core-contract.md` 作为单一契约源，并维持 `auto_evolve`、`check_r0_skill_record_dirs.py`、人工巡检三者的最低断言一致。
  - 继续执行 `dry-run -> apply -> check_skill_links -> remote sync` 的顺序，避免把“本地镜像一致”与“远端仓库已同步”混为一谈。
  - 把“remote push 前校验 tracked skill scope”保留为下一步低风险补丁建议，优先避免假成功，而不是扩展新的 `r0-*` 子技能。
  - 保持结果卡片、记录目录和 staged 清理规则的 checker 化，不再回退到口头提醒。
not_adopt:
  - 暂不引入更重的远端发布流水线或额外 agent 编排；当前主要收益仍来自 contract 对齐与同步门禁。
  - 暂不因为本轮无文案 drift 就修改全部 skill；当前收益不足以覆盖批量改写风险。
  - 暂不把网络可达性失败记成 skill bad case；它更接近执行环境阻断，而不是 skill 规则缺陷。
