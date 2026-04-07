question: 2026-03-31 当前，提示词、eval、长任务自动化、MCP/skill 治理有哪些一手实践值得收敛到 `r0-*` skills？
sources:
  - https://developers.openai.com/api/docs/guides/evals
  - https://developers.openai.com/api/docs/guides/background
  - https://developers.openai.com/api/docs/guides/tools
  - https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#structure-prompts-with-xml-tags
signals:
  - OpenAI `Working with evals` 文档在 2026-03-31 已把 `prompt optimizer`、`agent evals`、`trace grading` 放进同一评测/优化主线，说明 prompt 迭代应绑定评测而不是只改文案。
  - OpenAI `Background mode` 明确适合长时任务异步执行与轮询，但指出其会保留结果约 10 分钟且不兼容 ZDR；这意味着自动化任务应优先用异步 job 语义，而不是把所有长任务塞进前台单轮。
  - OpenAI `Using tools` 已把 `MCP and Connectors`、`Skills`、`Shell` 作为同级工具面，说明 skill contract 本质上属于工具治理，不应只当作文档约定。
  - MCP Security Best Practices（2025-11-25 版）强调 per-client consent、scope minimization、SSRF 防护、local server sandbox 与命令可见性；这直接支持对本地 skill/automation 增加最小权限和显式命令检查。
  - Anthropic 文档继续强调用稳定结构标签分隔 instructions/context/input/examples；对于 skill 说明和 result contract，这支持继续保持显式分段和字段名稳定，而不是自然语言散写。
adopt:
  - 继续把 shared contract 里的路径、暂存清理、结果卡片、记录目录写成可校验断言，并优先让 `auto_evolve_r0_skills.py` 兜底。
  - 对 recurring automation 保持 `dry-run -> apply -> verify -> sync` 的状态机，避免直接修改再回头解释。
  - 对 skill 文档继续保持强结构分段与固定字段名，必要时增加轻量断言，但避免引入过重模板。
  - 对远端同步继续使用显式脚本和显式分支，保持可回放和可审计。
not_adopt:
  - 暂不扩张新的 `r0-*` 子技能；当前问题主要是 contract drift，不是能力缺口。
  - 暂不把所有 skill 文档改写成 XML/DSL；现有 Markdown + checker 已足够，过度格式化会增大维护成本。
  - 暂不引入更重的远端自动发布流水线；当前三远端脚本已能满足同步需求，增量收益有限。
