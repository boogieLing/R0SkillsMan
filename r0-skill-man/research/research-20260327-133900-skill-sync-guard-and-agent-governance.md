question: 2026-03-27 时点下，prompt、eval、自动化与 agent/skill 治理还有哪些新信号，值得纳入 r0-* skill 体系，特别是同步与来源可信度约束？
sources:
  - https://platform.openai.com/docs/guides/prompt-caching
  - https://developers.openai.com/api/docs/guides/prompt-optimizer
  - https://platform.openai.com/docs/guides/evaluation-best-practices
  - https://platform.openai.com/docs/guides/graders
  - https://platform.openai.com/docs/guides/background
  - https://platform.openai.com/docs/guides/batch
  - https://platform.openai.com/docs/guides/flex-processing
  - https://platform.openai.com/docs/guides/tools-remote-mcp
  - https://www.anthropic.com/engineering/building-effective-agents
  - https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails
signals:
  - Prompt side: OpenAI 仍强调把稳定前缀与可复用示例放在 prompt 前部，以获得更稳定的 cache hit；Prompt Optimizer 进一步说明提示词优化应以明确目标和可测指标为前提，而不是纯手工润色。
  - Eval side: 官方最佳实践继续强调从最简单、可重复的数据集评测起步，并把 graders 挂到真实工作流级别；复杂 agent 的失败常来自工具调用、路由、状态管理而不只是答案质量。
  - Automation side: 对于长耗时或低实时性的演进任务，官方建议优先考虑 background、Batch、Flex 之类异步/低成本执行形态，而不是同步阻塞式轮询。
  - Governance side: Anthropic 的 agent 实践仍强调“小而确定的工作流优先于不受约束的 agent”，并建议把 guardrails、权限范围、人工确认点做成流程边界，而不是放在提示词末尾碰碰运气。
  - Skill ops side: 从这次 partial worktree case 可见，本地 skill 治理不只要校验 prompt/record contract，还要校验“来源可信度”。任何全局同步脚本都应先验证 source completeness，再执行副作用动作。
adopt:
  - 为 `scripts/sync_skill_links.sh` 增加默认阻断：当当前来源的 `r0-*` 数量少于目标技能根目录已有数量时，停止同步并要求显式 `--allow-partial`。
  - 在 README 中把“完整 skill 根目录”前提写明，避免手动 `ln -sfn` 流程绕过 guard。
  - 继续沿用共享 contract + 轻量 checker 的治理方式，把“来源可信度”加入同步类脚本的基础门禁。
  - 后续若恢复完整 `r0-skill-man` 脚本链，优先补一个专用 sync-check 命令，输出 source/destination counts、detached 状态、link targets 与阻断原因。
not_adopt:
  - 目前不把远程 MCP、复杂审批流或集中式注册表强塞进所有本地技能；当前问题首先是本地脚本 guard 缺失，不是平台能力不足。
  - 暂不强制为每个 `r0-*` skill 单独补 `SKILL.md`；在当前仓库缺少完整技能目录的情况下，先修共享脚本与 README，比写一组失真的文档更有价值。
