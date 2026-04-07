context: 2026-04-01 的 `r0-skill-evolution` 巡检中，`python3 r0-skill-man/scripts/auto_evolve_r0_skills.py --dry-run` 返回 `flagged=0`，但 `python3 r0-submit/scripts/check_r0_skill_record_dirs.py --repo-root /Volumes/R0sORICO/r0_work/r0-skills` 同时报告全部 10 个 `r0-*` skills 缺少“共享结果契约 + 摘要卡片约束提示”。
expected: `auto_evolve` 与 record checker 应共享同一套最低 contract 断言；若 checker 会阻断，auto-evolve 至少应在 dry-run/apply 阶段把同类问题标成 flagged。
actual: auto-evolve 只检查 shared contract、本地记录路径与 staged 清理规则，没有覆盖 shared result contract / `首屏摘要卡片` 约束，导致巡检闭环分叉；需要手动修 `SKILL.md` 后再跑 apply。
root_cause: 两个门禁脚本各自演化，checker 已升级到“共享结果契约 + 摘要卡片”断言，但 auto-evolve 仍停留在较早的 contract 子集，没有跟随 shared contract 升级。
fix_strategy: 在 `r0-skill-man/scripts/auto_evolve_r0_skills.py` 中增加与 checker 对齐的 result-contract token 检查；同时为所有 `r0-*` skills 的 shared contract 显式补一行“shared result contract / 共享结果契约”提示，消除模糊解释空间。
guardrail: 以后凡是 shared contract 新增断言，必须同步更新三处：`shared/r0-core-contract.md` 对应提示、`check_r0_skill_record_dirs.py`、`auto_evolve_r0_skills.py`；若三者任意一处缺失，记为 bad case。
