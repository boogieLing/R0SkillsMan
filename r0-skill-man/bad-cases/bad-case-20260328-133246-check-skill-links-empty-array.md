context: 在完整 skill 根目录运行 `bash scripts/check_skill_links.sh`，来源与目标数量都正常，但脚本在输出 `broken_links` 时直接崩溃。
expected: 当 `broken_links` 为空时，校验脚本应输出 `- <none>`，并继续完成 codex/claude 两个目标目录的检查。
actual: 脚本启用了 `set -euo pipefail`，在 `broken` 为空数组时执行 `print_list "broken_links:" "${broken[@]}"`，直接报 `unbound variable`，导致校验流程异常退出。
root_cause: `check_skill_links.sh` 对空数组展开不安全；虽然 `print_list` 本身能处理“无参数”，但调用点先在 shell 层展开了 `${broken[@]}`，被 `set -u` 拦截。
fix_strategy: 在 `inspect_target_dir` 内对 `entries` 和 `broken` 都先做长度判断；为空时调用 `print_list "..."`，非空时再展开数组。同步补到当前 worktree 与完整根目录脚本。
guardrail: 所有启用 `set -u` 的本地维护脚本，在输出数组或可选参数前都必须做长度判断；不能把“函数内部会处理空参数”当作调用层安全前提。
