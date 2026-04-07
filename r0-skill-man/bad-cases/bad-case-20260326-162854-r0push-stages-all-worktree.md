context: 已记录到一个提交链路坏例子，`r0push` 在某些场景下可能自动带入全部工作区改动，而不是只提交当前预期的 staged 内容。
expected: 提交自动化只能处理显式 staged 的变更，未暂存或无关工作区改动必须保持不提交。
actual: `r0push` 可能扩大提交范围，把全部工作区改动一起带入，导致“只提交 staged 内容”的假设失效。
root_cause: 提交技能和调用方此前默认依赖“r0push 只消费 staged diff”的隐式约定，但没有把这一点当作不可信前提做二次校验。
fix_strategy: 后续所有依赖 `r0push` 的技能和流程都不得再假设其只提交 staged 内容；在进入 `r0push` 前必须重新核对 `git status --short`、目标 diff 范围与提交意图，必要时拆分到独立工作树或显式阻断。
guardrail: 在 `r0-submit` 及相关提交自动化中加入提交前范围确认，若存在无关未提交改动则默认阻断或升级为人工确认；把“r0push 只提交 staged”从隐式假设改成明确禁止依赖的坏例子。
