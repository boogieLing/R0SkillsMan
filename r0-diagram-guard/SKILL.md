---
name: r0-diagram-guard
description: 对 writing 项目文章目录中的流程图资产执行“检查门禁 + 自动修复”。当用户提到“图黑块/图截断/图片导入错误/流程图丢失/占位图 45x13/需要批量清洗图资产/做 gate”时使用本技能。支持自动重建 mermaid 图、包装 SVG、移除无法修复的坏引用，并输出门禁报告。
---

# r0-diagram-guard

## Overview

对单篇文章的 `assets/diagrams` 做质量门禁，并自动修复可修复问题，避免黑块、截断、占位图进入最终稿或同步链路。

## Workflow

1. 识别目标文章目录（必须是单篇文章目录）。
2. 扫描该目录下所有 `.md` 文件中的流程图引用：`assets/diagrams/diagram-*`。
3. 执行门禁检查。
4. 启用自动修复（推荐 `gate-fix`）。
5. 复检并输出报告 `assets/diagrams/diagram_guard_report.json`。

## Gate Checks

- 引用文件存在。
- PNG 尺寸可读。
- PNG 不是占位图（`45x13` 或 `<=60x20`）。
- PNG 不低于最小阈值（默认 `120x40`）。
- SVG 不含 `foreignObject`（避免本地黑块渲染）。

详细规则见：`references/gate-rules.md`。

## Auto Fix Strategy

- 对含 `foreignObject` 的 SVG：若同名 PNG 存在，改写为 PNG 包装型 SVG。
- 对缺失/占位/过小 PNG：若同名 `.mmd` 存在，调用 `mmdc` 重建 PNG 与包装 SVG。
- 对仍无法修复的引用：可选开启 `--drop-unfixable-refs` 从 Markdown 中移除坏图引用。

Mermaid 渲染尺寸配置见：`references/diagram_profiles.json`。

## Scripts

### 主脚本

`scripts/diagram_guard.py`

常用命令：

```bash
# 推荐：门禁 + 自动修复 + 复检
~/.codex/skills/r0-diagram-guard/scripts/diagram_guard.py \
  --article-dir "/path/to/article-dir" \
  --mode gate-fix \
  --drop-unfixable-refs

# 只检查，不改文件
~/.codex/skills/r0-diagram-guard/scripts/diagram_guard.py \
  --article-dir "/path/to/article-dir" \
  --mode check
```

### 便捷入口

`scripts/run_diagram_guard.sh`

```bash
~/.codex/skills/r0-diagram-guard/scripts/run_diagram_guard.sh \
  "/path/to/article-dir" \
  --mode gate-fix \
  --drop-unfixable-refs
```

## Preconditions

- 本机可用 `python3`、`sips`、`npx`。
- Mermaid 自动重建依赖 `@mermaid-js/mermaid-cli`（脚本会通过 `npx` 调用）。
- 默认浏览器渲染器路径为 Microsoft Edge：
  `/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge`
  可通过 `--edge-path` 覆盖。

## Output Contract

执行结束必须提供：

1. `before` 问题数量
2. `after` 问题数量
3. `passed=true/false`
4. 报告路径：`assets/diagrams/diagram_guard_report.json`

门禁未通过时退出码为 `2`。
