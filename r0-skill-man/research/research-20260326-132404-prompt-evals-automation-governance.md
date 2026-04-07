question: 2026-03-26 时点下，prompt、eval、自动化与技能治理有哪些值得纳入 r0-* skill 体系的最新实践？
sources:
  - https://platform.openai.com/docs/guides/prompt-caching
  - https://platform.openai.com/docs/guides/graders
  - https://platform.openai.com/docs/guides/evaluation-best-practices
  - https://platform.openai.com/docs/guides/evals
  - https://platform.openai.com/docs/guides/background
  - https://platform.openai.com/docs/guides/batch
  - https://platform.openai.com/docs/guides/flex-processing
  - https://platform.openai.com/docs/guides/tools-remote-mcp
signals:
  - Prompt side: static instructions/examples should stay at the prompt prefix; dynamic content should move to the tail so cache hits are stable. For long repeated prefixes, prompt caching can materially cut latency/cost.
  - Eval side: OpenAI now emphasizes eval flywheels, dataset-backed iteration, and model/python/string graders instead of ad-hoc spot checks. Agent evals recommend workflow-level trace grading for orchestration failures.
  - Automation side: long-running jobs should move to background mode; high-volume, low-urgency workloads should prefer Batch or Flex instead of synchronous loops.
  - Tooling side: remote MCP/connectors are becoming the standard boundary for extending capabilities; tool approvals and connector scopes should be explicit in prompts/contracts.
  - Governance side: evals should be attached to upgrades and prompt changes, not only model releases; reproducible datasets and structured outputs matter more than free-form rubric prose.
adopt:
  - In r0-request and r0-work style prompts, keep invariant policy blocks before dynamic task context to align with prompt caching and reduce prompt drift.
  - For r0-skill-man, keep recommending dry-run first, then apply; record the exact checker/sync commands as reproducible eval steps.
  - When a skill evolves or a major prompt changes, require at least one explicit validation command or checker result in the final artifact.
  - When future automation needs scale or latency tolerance, prefer background/batch/flex patterns over naive synchronous polling loops.
  - Keep shared contract stable and push new policy through one shared file plus cheap validators, instead of duplicating free-form rules across every skill.
not_adopt:
  - Do not force Batch/Flex semantics into every local skill; current local filesystem workflows are usually small and interactive.
  - Do not add heavy remote-MCP requirements into all r0-* skills; only adopt where a skill truly needs external tools.
  - Do not auto-rewrite prompt bodies aggressively; keep auto-evolution limited to metadata-safe fixes and explicit manual review for behavioral changes.
