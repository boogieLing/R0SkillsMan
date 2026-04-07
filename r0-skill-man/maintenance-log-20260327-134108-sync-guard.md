date: 2026-03-27 13:41:08 CST
scope:
  - 为 `scripts/sync_skill_links.sh` 增加 partial source guard 与 `--allow-partial`
  - 新增 `scripts/check_skill_links.sh` 作为只读同步校验入口
  - 更新 README 的同步说明与手动链接风险提示
  - 记录 partial worktree 同步坏例子与最新治理研究
changes:
  - 新增 `collect_skill_dirs`、`count_existing_skill_links`、`assert_safe_source_layout`
  - 默认比较当前来源 skill 数量与 `~/.codex/skills` / `~/.claude/skills` 现有 `r0-*` 数量；来源更少时 exit 2
  - 新增只读校验脚本，输出 source count、目标目录条目和 broken links，并在异常时返回非零
  - 在真实 skill 根目录同步相同补丁，避免当前 worktree 与本地根目录漂移
validation:
  - 计划验证 1：在当前 detached worktree 运行 `bash scripts/sync_skill_links.sh`，应被 guard 阻断
  - 计划验证 2：运行 `bash scripts/check_skill_links.sh`，确认当前 skill 根目录与全局链接的一致性状态
decision:
  - 不使用当前 worktree 直接重建全局软链接
  - 当前 `/Volumes/R0sORICO/r0_work/r0-skills` 也不是完整来源，先只做校验，不做实际同步
