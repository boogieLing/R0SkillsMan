context: `prepare_submit_dry_run.py` 在真实仓库运行时仍引用旧的 `r0-review` 路径，导致 dry-run 编排无法找到 review baseline 脚本而直接失效。
expected: dry-run 编排应基于当前脚本目录或仓库内相对位置自动发现 `r0-review/scripts/r0-review_baseline.sh`，并在 helper 缺失时返回清晰错误。
actual: 旧实现依赖过期路径，真实仓库运行时报缺失 helper，dry-run 编排中断。
root_cause: 工具链路径解析使用了历史路径假设，没有把 `r0-submit` 与 `r0-review` 的相对仓库布局作为唯一可信来源，也没有在启动阶段做完整 helper 存在性校验。
fix_strategy: 重建最小 `r0-submit` / `r0-review` 脚本链；`prepare_submit_dry_run.py`、`prepare_submit_record.py`、`write_r0push_scope_record.py` 全部改为以当前脚本目录推导依赖路径，并在运行前显式检查 helper 存在。
guardrail: 后续所有本地技能工具链脚本都不得依赖旧绝对路径；启动时必须先验证所有必需 helper 存在，否则返回结构化错误并停止。
