---
name: r0-submit
description: Submission and push safety skill for wrapping up engineering work. Use when the user asks to prepare commits, validate push scope, run review-before-push, record submission evidence, or safely invoke the bundled r0push tool.
---

# r0-submit

You are a submission safety and delivery wrap-up skill. Your job is to make the final commit and push path explicit, reviewable, and recoverable.

================================================================================

SHARED CONTRACT (MANDATORY)

================================================================================

- Before execution, you MUST load `../shared/r0-core-contract.md`.
- Final output MUST follow the shared result contract: `首屏摘要卡片 -> 执行摘要 -> 关键产物 -> 验证 / 证据 -> 风险 / 下一步 -> 自动进化`.
- The local record directory for this skill is `./r0/submit/`.
- Every substantial submit or dry-run flow MUST leave a local record under `./r0/submit/`.

================================================================================

MISSION

================================================================================

- Never assume the bundled `r0push` tool only submits staged changes.
- Review before push when there is any uncertainty.
- Make scope, evidence, and rollback path explicit.
- Keep local records out of Git tracking.

================================================================================

REQUIRED FLOW

================================================================================

1. Run local record migration first when needed:

```bash
python3 scripts/migrate_r0_record_dirs.py --repo-root .
```

2. Prepare or refresh a submit record:

```bash
python3 scripts/prepare_submit_record.py --repo-root .
```

3. For a no-commit rehearsal, prefer:

```bash
python3 scripts/prepare_submit_dry_run.py --repo-root .
```

4. Before any real submit action, enforce scope validation with:

```bash
python3 scripts/check_r0push_scope.py --repo-root .
```

5. If the submit should really proceed, prefer the fixed absolute-path tool created by quick start:

```bash
$HOME/.local/bin/r0push fix "your commit message"
```

If `scripts/quick_start.sh` has already completed, this absolute path will be fixed to the synced skill tool. After namespace initialization, both the binary name and absolute path suffix will be renamed together with the chosen prefix.

6. Block the flow when:
   - there is no staged change
   - unrelated dirty files exist outside `r0/`, `r0-*`, and `.gitignore`
   - commit intent is unclear
7. If the submit proceeds, record:
   - commit grouping decision
   - pre/post git status summary
   - scope-check output
   - local artifact paths

================================================================================

GIT HYGIENE

================================================================================

- Ensure `.gitignore` contains both `r0/` and `r0-*/`.
- If local record files are staged, remove them from staging:

```bash
git restore --staged -- r0/ 'r0-*'
```

- Do not silently include unrelated changes.
- Prefer dry-run preparation when the worktree is not obviously clean and intentional.

================================================================================

AUTO EVOLUTION

================================================================================

- When submit safety fails because of missing helpers, missing records, or scope ambiguity, record a bad case under `./r0/submit/bad-cases/`.
- If repeated failures come from missing preflight checks, strengthen the scripts instead of relying on reminders.
