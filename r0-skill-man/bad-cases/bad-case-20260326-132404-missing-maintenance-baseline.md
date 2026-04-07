context: 首次运行 r0-skill-evolution 自动化，要求汇总 bad cases、研究外部实践、校验 shared contract，并把结果沉淀到本地记录目录。
expected: 仓库根目录已经存在 ./r0/skill-man/ 下的维护日志、bad case 与 research 基线，且 .gitignore 同时覆盖 r0/ 与 r0-*/。
actual: 执行前未发现任何 ./r0/skill-man/ 记录文件；根 .gitignore 仅忽略 r0/，缺少共享契约要求的 r0-*/ 兼容规则；当前 worktree 还是部分镜像，不能直接当作完整技能根目录。
root_cause: shared contract 在 2026-03-26 已要求统一到 ./r0/<skill-key>/ 并兼容历史 r0-*/，但仓库初始化后没有一次完整的 maintenance baseline run 来补齐本地记录和 ignore 兼容项。
fix_strategy: 补写首次 maintenance log、research note 与 bad case；在仓库根 .gitignore 增加 r0-*/；后续自动化每次运行都先检查 ./r0/skill-man/ 是否存在当日记录。
guardrail: 以后若 find ./r0/skill-man -type f 为空，自动化必须把“缺失演进基线”视为阻塞级 bad case；同步前先区分完整技能根目录与只读/镜像 worktree，避免误判同步范围。
