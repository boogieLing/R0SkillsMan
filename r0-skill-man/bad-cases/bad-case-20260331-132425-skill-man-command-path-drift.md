context: 在 `2026-03-31` 的 `r0-*` skills 巡检中，`r0-skill-man/SKILL.md` 指导执行 `python3 scripts/auto_evolve_r0_skills.py` 与 `python3 scripts/sync_r0_skills.py`，但仓库根目录下并不存在这两个脚本。
expected: 维护技能中的命令应直接指向真实存在的 bundled script，且从仓库根目录执行时能够一次成功。
actual: 按文档命令执行会报 `No such file or directory`；真实脚本位于 `r0-skill-man/scripts/`，需要人工重新定位后才能继续巡检。
root_cause: 技能文档在脚本目录下沉后未同步更新，导致“执行说明”与“仓库实际布局”漂移。
fix_strategy:
  - 将 `r0-skill-man/SKILL.md` 中的 auto-evolve 与 sync 命令统一改为 `python3 r0-skill-man/scripts/...`。
  - 在技能文档中显式要求：若命令路径与 bundled script 位置不一致，优先修正文档并记为 bad case。
guardrail:
  - 维护类技能每次改动脚本目录结构后，必须重跑文档中的命令样例。
  - 巡检脚本与技能文档路径必须做成同仓库相对路径，避免依赖人工记忆。
