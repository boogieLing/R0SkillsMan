date: 2026-03-27 13:39 CST
scope:
  - 为 `scripts/sync_skill_links.sh` 增加 partial source guard 与 `--allow-partial`
  - 更新 README 的同步说明与手动链接风险提示
  - 记录 partial worktree 同步坏例子与最新治理研究
changes:
  - 新增 `collect_skill_dirs`、`count_existing_skill_links`、`assert_safe_source_layout`
  - 默认比较当前来源 skill 数量与 `~/.codex/skills` / `~/.claude/skills` 现有 `r0-*` 数量；来源更少时 exit 2
  - 在真实 skill 根目录同步相同补丁，避免当前 worktree 与本地根目录漂移
validation:
  - 计划验证 1：在当前 detached worktree 运行 `bash scripts/sync_skill_links.sh`，应被 guard 阻断
  - 计划验证 2：在 `/Volumes/R0sORICO/r0_work/r0-skills` 运行相同脚本，应安全通过并保持现有链接
decision:
  - 不使用当前 worktree 直接重建全局软链接
  - 只在真实 skill 根目录上执行实际同步
