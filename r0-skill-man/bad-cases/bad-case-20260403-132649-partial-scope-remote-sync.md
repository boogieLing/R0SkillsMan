context: 在 `/Volumes/R0sORICO/r0_work/r0-skills` 执行 `./scripts/check_skill_links.sh` 与远端同步预演时，发现当前仓库只有少量 `r0-*` 文件处于 Git tracked scope，但 `~/.codex/skills` 与 `~/.claude/skills` 仍保留 11 个指向本仓库的 `r0-*` 入口，其中 7 个已经失效，另有 `r0-roadmap/` 目录存在于工作树但未进入 Git tracked scope。
expected: 远端同步脚本在任何 `git push` 之前，就应明确阻断 partial source / broken links / working-tree-only skill 目录，并给出需要人工确认的 override 提示。
actual: 旧版 `scripts/sync_all_remotes.sh` 会直接进入远端推送流程，只在第一个远端 `cggame` 的 DNS 解析失败后中止，无法提前暴露“本地 skill 受管范围已经漂移”的根因。
root_cause: 远端同步脚本缺少两个前置门禁：一是“当前 Git tracked `r0-*` scope 与本地安装根中的受管软链范围是否一致”，二是“远端 SSH 主机是否可解析/可达”的连通性预检。
fix_strategy: 为 `scripts/sync_all_remotes.sh` 增加 tracked-skill scope preflight、broken-link / untracked-skill blocker、`--allow-partial-scope` 显式覆盖参数，以及远端主机 DNS 预检；同时更新 README，明确远端同步的安全边界。
guardrail: 后续所有 `r0-*` skill 远端同步都先跑 scope preflight；若 `~/.codex/skills` 或 `~/.claude/skills` 仍存在指向本仓库已删除目录的软链，默认阻断；只有用户明确接受 partial source 风险时才允许 `--allow-partial-scope` 继续。
