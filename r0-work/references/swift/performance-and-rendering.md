# Swift Performance And Rendering

These rules are mandatory for SwiftUI / UIKit / AppKit work under `r0-work`.

## 1. Repeated Rendering Is A Bug Signal

- Treat unnecessary repeated rendering as a correctness and performance issue, not a cosmetic detail.
- Avoid state changes that fan out across unrelated views.
- Keep view-local transient state local; do not promote it to shared observable state without a concrete reason.
- Do not recreate observable objects, stores, or expensive formatters on every render path.

## 2. SwiftUI Rules

- Keep `body` cheap.
- Do not put expensive filtering, sorting, mapping, decoding, date formatting, or image preparation directly inside `body`.
- Precompute expensive values outside render paths or in controlled state transitions.
- Avoid unstable identity in `ForEach`, lists, navigation state, and diff-sensitive containers.
- Do not trigger side effects from `body`.
- Be explicit about ownership for `@State`, `@StateObject`, `@ObservedObject`, `@EnvironmentObject`, and `@Bindable`.
- Prefer `@StateObject` for owned long-lived reference models; avoid recreating them during view refresh.

## 3. UIKit / AppKit Rules

- Avoid repeated layout invalidation, recursive view updates, or redundant constraint churn.
- Reuse expensive views, layers, formatters, and image pipelines when ownership is stable.
- Keep scroll, animation, and resize paths free of blocking work.

## 4. Compute Budget

- Move expensive work off the main thread unless UI affinity is required.
- Use caching only when ownership, invalidation, and memory cost are clear.
- Do not introduce duplicate caches at multiple layers without necessity.
- Prefer incremental updates over recomputing whole view models or whole snapshots.

## 5. Verification Checklist

Before completion, explicitly review:

- repeated render triggers
- expensive work in render paths
- unstable identity / diff churn
- main-thread blocking work
- redundant subscriptions / publishers / observers
- duplicate computation across layers
