question: 2026-03-30 时点下，prompt、eval、自动化与 skill governance 的最新官方实践，哪些应继续收敛进 r0-* skill 体系？
sources:
  - https://developers.openai.com/api/docs/guides/prompt-caching
  - https://developers.openai.com/api/docs/guides/prompt-optimizer
  - https://developers.openai.com/api/docs/guides/evaluation-best-practices
  - https://developers.openai.com/api/docs/guides/graders
  - https://www.anthropic.com/engineering/building-effective-agents
  - https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
  - https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  - https://modelcontextprotocol.io/specification/2025-06-18
signals:
  - OpenAI Prompt Caching 明确要求把稳定指令和示例放在 prompt 前缀、把变量内容放在尾部，以便获得精确前缀缓存命中；这继续支持“shared contract 固定前置、任务上下文后置”的 skill 写法。
  - OpenAI Prompt Optimizer 已把“数据集 + grader + 后台优化”做成标准闭环，说明提示词治理不该停留在人工润色，而应绑定最少样本、grader 结果和人工批注后再优化。
  - OpenAI Graders / Evaluation Best Practices 继续强调细粒度 grader、可复跑基准与显式验证命令；这与 r0-* 当前的 dry-run / checker / evidence-first 输出方向一致。
  - Anthropic 在 2026-01-09 发布的 agent eval 文章明确把 transcript、outcome、grader、harness 区分开，并强调复杂 agent 的问题往往出在工具调用、状态推进和轨迹，而不只是最终答案。
  - Anthropic 的 building/effective agents 与 long-running harness 文章继续收敛到“先 workflow、后 agent；分步推进；留下清晰 artifacts；保持 clean state”，这与本地技能体系中的 maintenance log、bad case、research note 非常一致。
  - MCP 2025-06-18 规范把 Prompts、Resources、Tools、Roots、Sampling、Elicitation 明确成协议能力，并把 consent、tool safety、sampling controls 写成安全原则，说明 skill/automation 契约应该显式声明边界、同意点和工具能力。
adopt:
  - 保持 `shared/r0-core-contract.md` 作为单一约束源，并把“摘要卡片 + Record 路径 + validation 证据”继续收敛到轻量 checker，而不是分散到口头约定。
  - 保持提示词正文的稳定前缀结构，避免把动态上下文插入 policy 区域；后续对 `r0-request`、`r0-work`、`r0-skill-man` 的改写都应优先复用固定头部。
  - 对 skill 演进继续采用“dry-run -> checker -> apply -> sync”的可复跑闭环，并把验证命令写进 maintenance log。
  - 把长期自动化任务继续当作 harness 问题处理：留下 bad case、progress artifact、验证状态，而不是只依赖 session 内记忆。
  - 在 sync / tool 类脚本中继续显式保留 source completeness、tool safety 与 consent 风格约束，避免部分镜像或高权限副作用绕过门禁。
not_adopt:
  - 不把 Prompt Optimizer、grader API 或远程 MCP 强行嵌入每个本地 skill；当前本地技能治理仍以轻量文本契约和脚本门禁为主。
  - 不把简单维护流升级成多 agent 编排；官方结论仍然是优先 workflow，只有在评测证明必要时才增加 agent 复杂度。
  - 不把结果卡片规则写成更重的模板引擎或富文本卡片系统；共享 contract 的紧凑 Markdown 卡片已足够稳定。
