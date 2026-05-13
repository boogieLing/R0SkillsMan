# Swift Memory And Lifecycle

These rules are mandatory for long-lived Swift code, especially with SwiftUI, Combine, async/await, delegates, observers, and timers.

## 1. Memory Leaks Are Release Blockers

- Treat retain cycles, orphaned tasks, unbalanced observers, and long-lived strong reference chains as blocker-level risks.
- Every introduced reference type should have a clear ownership story.
- Every long-lived subscription or observer should have an explicit teardown path.

## 2. Closures And Captures

- Review every escaping closure for capture semantics.
- Use weak/unowned capture lists only when ownership is understood; do not cargo-cult them.
- Avoid capturing `self` strongly in:
  - timers
  - observers
  - callback registries
  - long-lived async work
  - Combine sinks / assignments

## 3. Async / Concurrency

- Tie tasks to lifecycle when possible.
- Support cancellation for long-lived or user-abandonable work.
- Do not let detached or background tasks outlive the feature scope without explicit design.
- Keep UI mutations on the correct actor, and avoid ping-ponging state across actors without need.

## 4. Observer Hygiene

- NotificationCenter, KVO, delegates, timers, display links, Combine pipelines, and async streams must have balanced registration and cleanup.
- Avoid duplicate observers/subscriptions caused by repeated lifecycle entry or repeated rendering.

## 5. Verification Checklist

Before completion, explicitly review:

- retain-cycle risk
- observer / timer cleanup
- task cancellation
- actor isolation correctness
- duplicate subscription paths
- reference ownership clarity
