# R0 Shared Contract

## 1. Local Record Layout

- 所有 `r0-*` skill 的本地文档、审查记录、执行总结、坏例子、研究笔记，统一写入 `./r0/<skill-key>/`。
- `<skill-key>` 固定为 skill 名去掉前缀 `r0-` 后的剩余部分，例如：
  - `r0-request -> ./r0/request/`
  - `r0-read -> ./r0/read/`
  - `r0-skill-man -> ./r0/skill-man/`
- 建议子目录：
  - `artifacts/`：脚本输出、临时分析结果
  - `bad-cases/`：失败案例、误判案例、回归案例
  - `research/`：联网研究记录、外部实践对标
- 所有本地记录默认视为“不进入版本控制”的本地资产。
- 若目标项目已存在历史目录 `r0-xxx/`，在写入新目录前必须先执行一次自动迁移：

```bash
python3 /Users/r0/.codex/skills/r0-submit/scripts/migrate_r0_record_dirs.py --repo-root .
```

- 迁移原则：
  - 直接把 `r0-xxx/` 迁到 `r0/xxx/`
  - 若目标文件已存在且内容相同，删除旧副本
  - 若目标文件已存在且内容不同，保留冲突并显式报告，禁止静默覆盖

## 2. Git Hygiene

- `.gitignore` 主规则统一为：`r0/`
- 为兼容历史遗留目录，目标项目还必须额外忽略：`r0-*/`
- 不再为单个 skill 分别维护 `r0-read/`、`r0-review/`、`r0-submit/` 这类旧路径规则，但必须避免旧目录重新进入版本控制。
- 若本地记录被误加入暂存区，统一执行：

```bash
git restore --staged -- r0/ 'r0-*'
```

- 若项目中已存在历史目录，如 `r0-read/`、`r0-review/`、`r0-work/`，保留其本地内容即可，但必须通过 `.gitignore` 保证这些目录继续不进入 Git 追踪。

## 3. Auto Evolution Loop

- 每次 skill 执行结束后，都要检查是否出现以下任一信号：
  - 失败或阻塞
  - 反复追问同类信息
  - 输出格式返工
  - 用户纠正了结果
  - 可预见的重复性人工操作
- 若出现上述信号，必须至少做下面一项：
  - 写入 `./r0/<skill-key>/bad-cases/` 记录坏例子
  - 写入 `./r0/<skill-key>/research/` 记录外部实践
  - 输出 Codex automation 建议，安排后续周期性自检或演进

### 3.1 Bad Case Capture

- 坏例子文件建议命名：
  - `bad-case-YYYYMMDD-HHMMSS-<slug>.md`
- 最少字段：
  - `context`
  - `expected`
  - `actual`
  - `root_cause`
  - `fix_strategy`
  - `guardrail`

### 3.2 Web Research

- 当任务涉及提示词、评测、自动化、工作流编排、模型能力边界、外部平台能力时，优先做联网研究。
- 研究应优先使用官方或一手资料；如果不是官方资料，必须明确这是推断或行业参考。
- 研究笔记建议命名：
  - `research-YYYYMMDD-HHMMSS-<slug>.md`
- 研究最少字段：
  - `question`
  - `sources`
  - `signals`
  - `adopt`
  - `not_adopt`

### 3.3 Codex Automation

- 当某个 skill 的演进动作具有重复性时，优先输出 `::automation-update{...}` 建议，而不是只留口头提醒。
- 自动化提示词只描述任务本身，不写调度和工作目录。
- 自动化目标优先包括：
  - 周期性汇总坏例子
  - 周期性搜索最新外部实践
  - 周期性校验共享输出结构与本地记录规范

## 4. Unified Result Contract

- 所有自然语言结果默认使用中文，除非 skill 自身明确要求其他语言。
- 最终结果优先按以下顺序输出：
  1. `首屏摘要卡片`
  2. `执行摘要`
  3. `关键产物`
  4. `验证 / 证据`
  5. `风险 / 下一步`
  6. `自动进化`
- `首屏摘要卡片` 应优先使用稳定、紧凑、带左边框的 Markdown 结构。
- 默认使用：
  - 一组简短的 `>` 引用块行，保留左边框
  - 仅放 4 到 6 条短元信息
  - 每行尽量短，避免长句塞进卡片内部
- 不默认使用富文本 / H5 卡片；只有用户明确要求且当前宿主渲染稳定时才使用。
- 超过一行宽度的详细说明，不要继续塞进卡片；移到卡片后的 `执行摘要` 或 `关键产物`。
- 除非宿主明确渲染稳定，否则不要默认使用：
  - 富文本 / H5 卡片
  - 宽表格
  - 依赖对齐的伪表格
- 卡片标题不要固定写“结果卡片”。
- 标题格式统一为：`随机颜表情 + 本次需求/结果总结`。
- 颜表情不要固定，必须从不同风格中随机选择，避免每次都复用同一个样式。
- 标题应短、可扫读、能直接概括当前任务，例如：
  - `ヽ(•̀ω•́ )ゝ 统一 r0 skill 本地记录规则`
  - `(╭☞•́⍛•̀)╭☞ 完成 skill 同步与契约校验`
  - `ᕙ(`▽´)ᕗ 强化 Swift 安全与性能门禁`
- 推荐卡片骨架：

```md
> **ヽ(•̀ω•́ )ゝ 本次需求总结**
> Skill: `r0-xxx`
> Status: `done | partial | blocked`
> Scope: `...`
> Output: `...`
> Validation: `pass | partial | fail`
> Record: `./r0/xxx/...`
```

- 若宿主支持结构化 directive，允许在正文后追加：
  - `::automation-update{...}`
  - `::code-comment{...}`
  - 其他宿主支持的卡片型指令
