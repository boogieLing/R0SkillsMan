# Swift Engineering References (r0-work)

Use these references when the primary implementation language is `swift`, or when the task is mainly for iOS, macOS, SwiftUI, AppKit, or UIKit.

## Loading Order

1. Always load `security-and-compliance.md` first.
2. Then load `performance-and-rendering.md` for UI, state, rendering, responsiveness, or performance-sensitive work.
3. Then load `memory-and-lifecycle.md` for async work, observers, closures, delegates, Combine, NotificationCenter, timers, or long-lived objects.

## Priority Order

For Swift / Apple-platform work, priority is always:

1. Security and compliance
2. Correctness and platform safety
3. Performance and rendering efficiency
4. Maintainability and readability

## Non-Negotiable Rules

- Do not weaken platform security settings just to “make it work”.
- Do not bypass entitlements, sandbox, ATS, Keychain, or privacy permission rules without explicit user instruction and visible justification.
- Do not introduce repeated rendering, redundant recomputation, retain cycles, or unbounded observers/timers.
- Do not guess Apple-platform behavior when repository evidence or platform constraints say otherwise.
