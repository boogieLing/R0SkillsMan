date: 2026-03-30 14:33:31 CST
scope:
  - 巡检 `r0-*` skills 的 shared contract、本地记录路径与结果卡片约束
  - 对标最新 prompt、eval、自动化与 skill governance 官方实践
  - 执行同步校验并在安全时做实际同步
changes:
  - 修复 `r0/submit/scripts/check_r0_skill_record_dirs.py` 的根目录探测错误，新增可用的 `--repo-root` 参数
  - 扩展 checker：同一脚本同时校验 shared contract、本地记录路径与摘要卡片约束
  - 为 `r0-question`、`r0-request`、`r0-skill-man` 补充更统一的共享结果契约/摘要卡片表述
  - 新增本轮 research note 与 bad case 记录，补充 2026-03-30 官方实践对标
validation:
  - `python3 /Volumes/R0sORICO/r0_work/r0-skills/r0/submit/scripts/check_r0_skill_record_dirs.py --repo-root /Volumes/R0sORICO/r0_work/r0-skills` => pass
  - `bash /Volumes/R0sORICO/r0_work/r0-skills/scripts/check_skill_links.sh` => pass
  - `python3 /Volumes/R0sORICO/r0_work/r0-skills/r0-skill-man/scripts/sync_r0_skills.py --dry-run` => all `no changes`
  - `python3 /Volumes/R0sORICO/r0_work/r0-skills/r0-skill-man/scripts/sync_r0_skills.py` => all `no changes`
decision:
  - 本轮实际同步是安全的，因为 dry-run 已确认 10 个 skills 在 `/Volumes`、`~/.codex/skills`、`~/.claude/skills` 间没有漂移
  - 不触碰仓库中已有的无关脏变更：`scripts/check_skill_links.sh` 与未跟踪 zip 资产保持原样
residual_risk:
  - `auto_evolve_r0_skills.py --dry-run` 仍报告 10 个 skills 可做元数据自动修复，说明 metadata 层还有单独收敛空间，但不属于本轮必须修复项
  - 当前工作树 `/Users/r0/.codex/worktrees/894f/r0-skills` 并不是完整 `r0-*` 技能源；持续维护仍应以 `/Volumes/R0sORICO/r0_work/r0-skills` 为可信根目录
