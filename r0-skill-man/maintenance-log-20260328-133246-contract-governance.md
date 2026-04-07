date: 2026-03-28 13:32 CST
scope:
  - 巡检 `r0-*` skills 的 shared contract、本地记录路径与结果卡片约束
  - 调研最新 prompt、eval、自动化与技能治理实践
  - 执行 r0 skill 同步校验，并在安全范围内做实际同步
changes:
  - 复跑 `python3 r0/skill-man/scripts/auto_evolve_r0_skills.py --dry-run`，确认初始状态为 `flagged=9`
  - 为 `r0-question`、`r0-skill-man`、`r0-diagram-guard`、`r0-ios-agents`、`r0-read`、`r0-review`、`r0-submit`、`r0-work`、`r0-write-lark` 补充 shared contract / git hygiene / 结果卡片收敛文案
  - 复跑 auto-evolve dry-run，状态收敛为 `flagged=0`
  - 发现并修复 `scripts/check_skill_links.sh` 在 `set -u` 下空数组展开导致的校验崩溃
  - 执行 `python3 r0/skill-man/scripts/sync_r0_skills.py`，实际同步了 `shared/` 到 `/Users/r0/.codex/skills/shared`
validation:
  - `python3 /Volumes/R0sORICO/r0_work/r0-skills/r0/skill-man/scripts/auto_evolve_r0_skills.py --dry-run` => `updated=9, no_change=1, flagged=0`
  - `bash /Volumes/R0sORICO/r0_work/r0-skills/scripts/check_skill_links.sh` => `[OK] 未发现来源数量异常或失效软链接。`
  - `bash /Users/r0/.codex/worktrees/b98e/r0-skills/scripts/check_skill_links.sh` => 仍按预期 `exit_code=2`，因为当前 worktree 仅含 2 个 skill，来源不完整
  - `python3 /Volumes/R0sORICO/r0_work/r0-skills/r0/skill-man/scripts/sync_r0_skills.py` => `shared` 更新 1 个文件，其余 `r0-*` skills 无漂移
decision:
  - 不在当前部分 worktree 上执行全局软链接重建
  - 将完整 skill 根目录 `/Volumes/R0sORICO/r0_work/r0-skills` 继续视为安全同步源
  - `bash scripts/sync_skill_links.sh` 在本轮仍受沙箱权限限制，故只保留校验与非破坏性同步结果
residual_risk:
  - 当前 Git 仓库只追踪少量脚本与共享 contract，许多 `r0-*` skill 文档仍是本地资产；后续若希望版本化治理，需要先明确“repo source of truth”
  - `scripts/sync_skill_links.sh` 的实际软链接写入仍需要在具备目标目录写权限的环境中执行
