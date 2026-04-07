context: `r0-skill-man` 的 `legacy_path_issues()` 只检查 `git restore --staged r0/`，没有要求同时覆盖历史目录 `r0-*`。
expected: shared contract 变更后，自动巡检应把缺失 `git restore --staged -- r0/ 'r0-*'` 的 skill 标为 drift，并推动同类最小修复。
actual: 初次 dry-run 对 `r0-skill-man` 仍报 green；收紧校验逻辑后，才额外暴露 `r0-diagram-guard`、`r0-ios-agents`、`r0-question`、`r0-write-lark` 四个同类遗漏。
root_cause: skill 自身文案和 auto-evolve checker 同时滞后于 shared contract，导致“规范升级但门禁未升级”的假阴性。
fix_strategy: 同步修正文案与 checker；把 legacy staging cleanup 视为 shared contract 的强约束，而不是建议项。
guardrail: 后续凡是 shared contract 涉及路径、`.gitignore`、暂存清理、结果卡片字段的升级，必须同步补 `auto_evolve_r0_skills.py` 的显式断言。
