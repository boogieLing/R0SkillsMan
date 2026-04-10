---
name: r0-skill-man
description: "Deterministic daily maintenance for local skill ecosystems: clean obsolete skills, audit and refactor remaining skills, extract recent pitfalls, and write a structured execution log. Use when running recurring skill governance, entropy control, quality gates, or system-level skill evolution."
---

# R0 Skill Man

## Shared Contract

- Execute only after loading `../shared/r0-core-contract.md`.
- Result output MUST follow the shared result contract / 共享结果契约: start with the unified `首屏摘要卡片`, then provide structured sections and `自动进化`.
- The local record directory for this skill is `./r0/skill-man/`.
- Every maintenance cycle MUST leave its execution record, bad cases, and research notes under `./r0/skill-man/`.
- `.gitignore` main rule MUST be `r0/`, and the repo SHOULD keep compatibility rule `r0-*/`.
- If local records were staged by mistake, run `git restore --staged -- r0/ 'r0-*'`.

Execute a conservative, deterministic maintenance cycle for local skills.
Prioritize stability, backward compatibility, and entropy reduction.

## Inputs

Require these runtime inputs before acting:
- Target roots to scan for skills (default order):
  - `~/.codex/skills`
  - `~/.agents/skills`
  - User-provided workspace skill root (if any)
- Current date in local timezone
- Optional scope filter (single root or full local ecosystem)

Treat a skill as a directory containing `SKILL.md`.

## Non-Negotiable Operating Rules

- Delete only with high confidence.
- Prefer strengthening over creating new skills.
- Prefer deduplication over proliferation.
- Keep changes minimal and reversible.
- Preserve existing skill names unless rename is required for correctness.
- If required evidence is missing, flag instead of deleting.

## Daily Maintenance Cycle

Run the following steps in order.

### Step 1: Clean Unused or Obsolete Skills

1. Build skill inventory.
   - Scan target roots for `*/SKILL.md`.
   - Record: skill path, name, description, last modified time, duplicate-name conflicts.
2. Check active references.
   - Search local repositories/workflows for explicit skill mentions (for example: `$skill-name`, skill folder names, or SKILL path references).
   - Use evidence tiers to avoid false positives:
     - Tier-1 (strong): explicit invocation tokens such as `$skill-name` in prompts, automations, or runbooks.
     - Tier-2 (weak): plain skill-name or SKILL path mentions in registry/listing files.
   - Classification rule:
     - Treat Tier-1 as active usage evidence.
     - Treat Tier-2-only hits as insufficient evidence; use `flag_candidate` unless other proof exists.
   - Exclude noisy locations from reference counting by default:
     - `**/AGENTS.md`
     - `**/SKILL.md`
     - `**/logs/**`
     - `**/sessions/**`
     - `**/.git/**`
3. Classify each skill:
   - `delete_candidate`: clear duplicate/redundant/obsolete and no active references.
   - `flag_candidate`: uncertain usage or insufficient evidence.
   - `retain`: active or unique capability.
4. Delete only when all are true:
   - No active references found.
   - Functionality is duplicated or clearly obsolete.
   - Deletion does not break known workflows.
5. If any uncertainty remains, do not delete.

Produce structured output:
- Deleted Skills (with reason)
- Flagged Skills (with reason)
- Retained Skills
- If none deleted: `No cleanup required.`

### Step 2: Audit and Update Remaining Skills

For each retained skill, evaluate:
- Outdated logic
- Inconsistent structure
- Ambiguous naming or trigger description
- Weak output contract
- Misalignment with current AI-SOP workflow
- Entropy impact (reduces vs increases complexity)

Update only when improvement is clear and material.

Allowed updates:
- Refine frontmatter description trigger clarity
- Tighten workflow steps and constraints
- Standardize deterministic output schema
- Remove redundant or ambiguous instructions
- Align with current engineering workflow expectations

Required report fields:
- Updated Skills
- Change Summary
- Reason for Update
- Unmodified Skills (mark `No update required` where applicable)

Default low-risk auto-evolution action:
- From the repo root, run `python3 r0-skill-man/scripts/auto_evolve_r0_skills.py` before manual Step 2 edits.
- Allow this auto step to update only metadata-level issues:
  - Missing or stale `agents/openai.yaml`
  - Validation-safe frontmatter consistency checks
- If the auto step flags a skill, do not force-fix blindly; move it to manual review.

### Step 3: Extract Pitfalls and Evolve System

Review recent patterns from available local evidence (recent edits, repeated fixes, recurring manual tasks, output inconsistencies).
Then perform web research for the latest external practices around prompts, evals, agent orchestration, automation, and skill maintenance when the topic is time-sensitive.

Identify issues:
- Repeated mistakes
- Manual repetitive operations
- Prompt structural weaknesses
- Inconsistent output formats
- High cognitive-load handoffs
- Missing skill support
- External practice drift discovered via web search

For each issue, decide exactly one action:
- Strengthen an existing skill
- Create a narrowly scoped sub-skill
- No action

Apply enhancement only when benefit is clear and recurring.
If none is justified, output exactly:
- `No structural enhancement required.`

### Step 4: Write Execution Log

Write a deterministic log file under:
- Primary: `/Volumes/R0sORICO/r0_work/r0-skills/r0/skill-man`
- Fallback (when primary is missing or not writable): `$CODEX_HOME/automations/r0/skill-man`

Default filename:
- `skill-maintenance-YYYY-MM-DD.md`

If file already exists for the day, append a new run section instead of overwriting.
Always report the actual absolute path used.

Log template:

```markdown
Date:
Skill Count Before:
Skill Count After:
Cleanup Summary:
Update Summary:
Enhancement Summary:
Bad Case Summary:
Research Summary:
Automation Suggestion:
System Entropy Trend (Increase / Stable / Decrease):
Overall System Health (Low / Medium / High Stability):
Next Suggested Evolution:
```

Log quality constraints:
- Concise
- Technical
- Deterministic
- Non-emotional
- No unnecessary verbosity

## Execution Contract

When invoked, always return:
1. `首屏摘要卡片`
2. `Maintenance Scope`
3. `Step 1 Result`
4. `Step 2 Result`
5. `Step 3 Result`
6. `Log File Written`
7. `Risk Notes` (only if action risk exists)
8. `自动进化`

Do not return speculative claims as facts.
If evidence is missing, say so explicitly and choose conservative action.

## Minimal Command Patterns

Use fast local commands to reduce overhead:
- Inventory: `rg --hidden --files -g '**/SKILL.md' <roots>`
- Reference checks (Tier-1 first): `rg -n --hidden -g '!**/AGENTS.md' -g '!**/SKILL.md' -g '!**/logs/**' -g '!**/sessions/**' '\$<skill-name>' <search-roots>`
- Reference checks (Tier-2 fallback): `rg -n --hidden -g '!**/logs/**' -g '!**/sessions/**' '<skill-name>|/<skill-dir>/SKILL.md' <search-roots>`
- Duplicate name checks: parse frontmatter `name:` across all `SKILL.md`

Prefer deterministic filesystem evidence over memory-based assumptions.

## Bidirectional R0 Sync

Use the bundled script to keep `r0-` skills synchronized between local roots and the mirror workspace.

Default roots:
- `/Users/r0/.codex/skills`
- `/Volumes/R0sORICO/r0_work/r0-skills`

Command patterns:
- Dry run: `python3 r0-skill-man/scripts/sync_r0_skills.py --dry-run`
- Apply sync: `python3 r0-skill-man/scripts/sync_r0_skills.py`
- Apply + prune extra files: `python3 r0-skill-man/scripts/sync_r0_skills.py --prune`

Sync policy:
- Discover skills by prefix + `SKILL.md`.
- Use newest copy as source of truth per skill.
- Propagate source to other roots.
- Do not delete unless `--prune` is explicitly set.

## Auto Evolution Commands

Use these commands to evolve local `r0-` skills conservatively:
- Dry run: `python3 r0-skill-man/scripts/auto_evolve_r0_skills.py --dry-run`
- Apply: `python3 r0-skill-man/scripts/auto_evolve_r0_skills.py`

Evolution policy:
- Prioritize low-risk deterministic repairs.
- Keep high-risk content rewrites out of automatic mode.
- Treat flagged skills as manual-review items.
- If the command path in this document diverges from the bundled script location, patch the document first and record the drift as a bad case.
