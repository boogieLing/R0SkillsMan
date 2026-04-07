context: 在 `2026-03-30` 巡检中，执行 `python3 /Volumes/R0sORICO/r0_work/r0-skills/r0/submit/scripts/check_r0_skill_record_dirs.py --repo-root /Volumes/R0sORICO/r0_work/r0-skills` 时，脚本直接返回“未找到 r0-* skill 文件”。
expected: checker 应能在真实 skill 根目录上扫描 `r0-*/SKILL.md`，并校验 shared contract、本地记录路径和结果卡片约束。
actual: 脚本把 `SKILLS_ROOT` 固定为 `Path(__file__).resolve().parents[2]`，实际落在 `/Volumes/R0sORICO/r0_work/r0-skills/r0/`，导致根目录错位；同时传入的 `--repo-root` 参数完全未被消费。
root_cause: checker 依赖硬编码层级推断仓库根目录，且 CLI 参数设计与实现脱节，导致脚本无法在源仓库或镜像仓库中可靠自举。
fix_strategy:
  - 为脚本增加 `--repo-root` 参数解析，并让其真正控制扫描根目录。
  - 默认通过搜索 `shared/r0-core-contract.md` 自动探测 repo root，降低层级耦合。
  - 把 shared contract 与结果卡片提示一并纳入 checker，避免后续继续人工扫文本。
guardrail:
  - 后续凡是 `r0-*` 合规检查脚本，必须至少支持一个显式根目录参数。
  - 真实仓库根目录自举通过应成为最低验证项，不能只在单一脚本相对路径下工作。
