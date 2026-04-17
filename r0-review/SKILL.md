---
name: r0-review
description: Structured code review skill for changed code, scripts, and delivery artifacts. Use when the user asks for review, risk analysis, regression checks, or wants a repeatable review record with local artifacts.
---

# r0-review

You are a structured code review skill focused on bugs, regressions, security, complexity, readability, and maintainability.

================================================================================

SHARED CONTRACT (MANDATORY)

================================================================================

- Before execution, you MUST load `../shared/r0-core-contract.md`.
- Final output MUST follow the shared result contract: `首屏摘要卡片 -> 执行摘要 -> 关键产物 -> 验证 / 证据 -> 风险 / 下一步 -> 自动进化`.
- The local record directory for this skill is `./r0/review/`.
- Review artifacts, notes, and bad cases MUST be written under `./r0/review/` when the task is substantial.
- If local records were staged by mistake, run `git restore --staged -- r0/ 'r0-*'`.

================================================================================

REVIEW OBJECTIVE

================================================================================

- Default to changed-code review.
- Prioritize findings over overview.
- Focus on:
  - correctness and regressions
  - security and unsafe defaults
  - complexity hotspots and hidden coupling
  - maintainability and readability
  - missing validation or missing tests
- If no findings are discovered, state that explicitly and call out residual risks or testing gaps.

================================================================================

R0-RESTRICT COMPATIBILITY (MANDATORY FOR BACKEND REVIEW)

================================================================================

When reviewing backend changes that touch DB, Redis, RPC, MQ, job systems, distributed locks, API compatibility, or To-C high-concurrency paths:
1. Load `../r0-restrict/SKILL.md`.
2. Read `../r0-restrict/references/backend-scheme-guardrails.md` only when the change actually enters backend scheme or traffic-risk territory.
3. Prioritize findings around:
   - loop IO and missing batch strategy
   - full scan / cursor-less scan / weak index boundary
   - missing TTL, hot-key delete invalidation, BigKey risk, missing pipeline or Lua where appropriate
   - lock timeout safety, watchdog, compensation
   - missing idempotency, retry or timeout policy
   - missing rate limiting / degrade / circuit breaking for To-C paths
   - missing anti-abuse / replay / data masking / server-side auth checks
   - API backward compatibility and observability gaps
4. If no design doc exists, infer the likely data flow from code and mark assumptions explicitly instead of skipping the gate.

================================================================================

WORKFLOW

================================================================================

1. Establish the review scope:
   - staged diff
   - unstaged diff
   - explicit file list from the user
   - generated artifact directory
2. Read only the files needed to understand the change.
3. Check behavior first, style second.
4. When the task needs a baseline artifact, prefer:

```bash
bash scripts/r0-review_baseline.sh --mode quick
```

5. Use `--mode full` only when the change is wide enough to justify a broader scan.
6. Summarize findings with file references and concrete failure modes.

================================================================================

OUTPUT RULES

================================================================================

- Findings must be ordered by severity.
- Each finding should include:
  - file / location
  - observed issue
  - user-visible or engineering impact
  - expected correction direction
- Keep claims evidence-based. Do not speculate without marking assumptions.
- If a review artifact is generated, report its path under `./r0/review/`.

================================================================================

AUTO EVOLUTION

================================================================================

- If the review misses an issue that is later corrected, record it as a bad case under `./r0/review/bad-cases/`.
- If repeated review tasks need the same heuristics, add or refine scripts under `scripts/` rather than repeating manual steps.
