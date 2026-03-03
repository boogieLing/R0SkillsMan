# Orchestration Matrix

## Quick Route

| Scenario | Primary Skills | Parallel Lanes | Mandatory Gates |
|---|---|---|---|
| Figma to new SwiftUI screen | `figma`, `figma-implement-design`, `swiftui-expert-skill` | UI + behavior/tests | Design fidelity, engineering |
| Existing screen redesign | `figma`, `swiftui-expert-skill`, `mobile-ios-design` | Layout refactor + accessibility | Design fidelity, HIG, accessibility |
| Motion polish | `swiftui-animation`, `swiftui-expert-skill` | Motion + regression tests | HIG, reduced motion, engineering |
| Accessibility remediation | `accessibility-compliance`, `screen-reader-testing` | A11y fixes + screen reader validation | Accessibility, engineering |
| End-to-end feature (design + logic) | `figma`, `figma-implement-design`, `swiftui-expert-skill`, `accessibility-compliance` | UI lane + logic lane + quality lane | All gates |

## Dependency Heuristics

Run in parallel when:
- files and ownership are disjoint
- no shared API/view-model contract is changing
- acceptance criteria are independent

Run serially when:
- multiple tasks edit the same core state model
- design contract is still unstable
- test baseline is failing and root cause is unknown

## Escalation Rules

If any gate fails:
1. Stop downstream tasks that depend on the failed gate.
2. Patch the minimum failing scope first.
3. Re-run only affected validations, then resume blocked lanes.
