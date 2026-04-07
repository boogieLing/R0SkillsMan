---
name: r0-ios-agents
description: Orchestrate Codex-based iOS app development by coordinating multiple local skills (especially Figma-to-code and SwiftUI skills) through dependency-aware execution. Use when requests involve end-to-end iOS delivery, multi-skill coordination, parallel workstreams, milestone planning, or converting Figma designs into production SwiftUI with staged validation.
---

# r0-ios-agents

## Shared Contract

- 执行前必须加载 `../shared/r0-core-contract.md`。
- 结果输出必须遵循 shared result contract / 共享结果契约：先给统一的 `首屏摘要卡片`，再给结构化正文与 `自动进化`。
- 本技能的本地记录目录固定为 `./r0/ios-agents/`。
- 每次编排结束后，必须把计划、执行、门禁结果和演进项写入 `./r0/ios-agents/`。
- `.gitignore` 统一规则为 `r0/`。
- 若本地记录被误加入暂存区，执行 `git restore --staged -- r0/ 'r0-*'`。

## Overview

Use this skill as the top-level scheduler for iOS app work. It decides which skill to run, in what order, and which streams can run in parallel.

Load `references/orchestration-matrix.md` when selecting lanes and gates.

## Intake Contract

Collect or infer:
1. Product scope (MVP, feature, refactor, bugfix)
2. Design source (Figma URL/node IDs or no design)
3. Tech baseline (SwiftUI/UIKit, iOS minimum version, existing modules)
4. Constraints (deadline, accessibility, animation quality, CI/testing target)

If design inputs are missing for design-led requests, ask for Figma link/node IDs first.

## Skill Routing

Default skill set for Codex + Figma + iOS:
1. `figma`: read design context, tokens, assets, dimensions
2. `figma-implement-design`: convert selected nodes to implementation targets
3. `swiftui-expert-skill`: produce/adjust production SwiftUI code
4. `mobile-ios-design` + `apple-hig-designer`: align UX with iOS HIG
5. `swiftui-animation`: implement interactions and transitions
6. `accessibility-compliance`: apply WCAG/mobile accessibility checks
7. `screen-reader-testing`: validate VoiceOver flows when UI changes are significant

Skip skills that are not required by the request.

## Orchestration Model

Use a DAG-style plan, not a strict linear chain.

### Lane A: Discovery
- Read requirements and repository context
- Pull Figma context if provided
- Define acceptance criteria and checkpoints

### Lane B: UI Build
- Implement static UI and design tokens
- Map components to feature modules

### Lane C: Behavior & Quality
- Implement state/data flow and error states
- Add accessibility semantics and motion adjustments
- Add or update tests

Run Lane B and Lane C in parallel after Discovery unless blocked by unresolved component contracts.

## Gates

Do not move forward without passing each gate:
1. Design fidelity gate: spacing/typography/colors/components match intent
2. HIG gate: navigation, touch targets, platform patterns are native
3. Accessibility gate: labels, focus order, dynamic type, reduced motion
4. Engineering gate: build passes and tests are updated for changed behavior

## Execution Rules

1. Start with a short dependency plan identifying parallelizable tasks.
2. Prefer parallel execution when tasks touch different files or concerns.
3. Serialize when there is a shared contract risk (same view model/API/schema).
4. After each lane finishes, publish concise status and blockers.
5. If blockers appear, re-plan DAG edges instead of forcing a linear flow.

## Output Format

For each coordinated task, output:
1. `首屏摘要卡片`: 标题使用“随机颜表情 + 本次需求总结”，并包含 status, scope, validation, local record
2. `Plan`: lanes, dependencies, and gate criteria
3. `Execution`: what was done per lane and by which skill
4. `Validation`: gate results with concrete evidence
5. `Next`: remaining work or handoff
6. `自动进化`: bad cases, external research, automation suggestion

If a coordination pattern repeatedly fails, or an upstream platform/design workflow changed, capture it under:
- `./r0/ios-agents/bad-cases/`
- `./r0/ios-agents/research/`
