context: 在只包含 `r0-review` 与 `r0-submit` 的临时 worktree 中执行 `scripts/sync_skill_links.sh`，会把现有 `~/.codex/skills` / `~/.claude/skills` 的同名链接切到错误来源。
expected: 链接同步脚本应先校验当前仓库是否像“完整 skill 根目录”；若目标目录已有更多 `r0-*` 技能，而当前来源只包含其中一部分，应默认阻断并要求显式确认。
actual: 旧实现会直接遍历当前 worktree 中存在的 `r0-*` 目录并重建对应软链接，没有任何“部分镜像”防护。
root_cause: 同步脚本默认把“当前工作目录”视为可信完整源，但自动化常在 detached worktree 或裁剪镜像中运行，这个前提并不成立。
fix_strategy: 在 `scripts/sync_skill_links.sh` 中增加来源完整性 guard；比较当前仓库里的 `r0-*` 数量与目标技能根目录已有的 `r0-*` 数量，发现来源更少时直接阻断，必要时通过 `--allow-partial` 显式放行。
guardrail: 任何会重建全局软链接、覆盖全局配置或写入共享目标目录的维护脚本，都必须先验证“当前来源是否完整且可信”；不能默认接受任意 worktree。
