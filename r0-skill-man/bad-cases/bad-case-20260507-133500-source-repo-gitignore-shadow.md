context: 2026-05-07 的 `r0-skill-evolution` 巡检中，新建 `r0-skill-man/scripts/check_r0_shared_contract.py` 与 `shared_contract_checks.py` 后，`git status --short --untracked-files=all` 只显示已修改文件，不显示这两个新脚本。
expected: 在 `r0-*` skill 源码仓库新增脚本后，`git status` 应直接暴露未跟踪文件，便于正常纳入版本控制。
actual: `git check-ignore -v` 显示仓库根 `.gitignore` 的 `r0-*/` 规则把 `r0-skill-man/scripts/check_r0_shared_contract.py` 与 `shared_contract_checks.py` 视为 ignored；新增源码文件会被静默吞掉。
root_cause: shared contract 把“普通目标项目需要兼容旧 `r0-*` 本地记录目录”的规则直接搬进了 skill 源码仓库根 `.gitignore`，但该仓库本身就跟踪 `r0-*` 目录，导致裸 `r0-*/` 与源码树命名冲突。
fix_strategy: 从 skill 源码仓库根 `.gitignore` 移除裸 `r0-*/`；把 shared contract 与 checker 改成条件规则：普通目标项目需要 `r0-*/`，source repo 只保留 `r0/`，并显式禁止在根 `.gitignore` 使用裸 `r0-*/`。
guardrail: 后续凡是要求“兼容旧本地记录目录”的 ignore 规则，都必须先验证它不会屏蔽 source repo 下新增的 `r0-*` 源码文件；至少执行一次 `git check-ignore -v <new-file>` 作为回归门禁。
