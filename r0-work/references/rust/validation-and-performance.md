# Validation And Performance (Rust / r0-work)

## Required Verification Angles

- Build / type-check evidence (`cargo check`, targeted build, or repository-equivalent command)
- Targeted test evidence for changed modules
- Async lifecycle evidence: task ownership, cancellation, shutdown, timeout behavior
- Blocking isolation evidence: whether blocking work is absent or explicitly isolated
- Observability evidence: logs, tracing, metrics, or a clear note that they are missing

## Rust Backend Review

- Review shared-state synchronization and lock scope.
- Review whether request handlers or service methods accidentally hold locks, buffers, or large owned values across await points.
- Review whether retries, reconnects, or background supervisors have bounded lifecycle and explicit failure surfacing.

## Operator / Compute Review

- Review batch size assumptions, memory growth risks, clone / copy behavior, and intermediate materialization.
- Review null / type / schema edge cases for custom compute logic.
- Review whether the implementation preserves predictable throughput under realistic batch or stream sizes.

## Performance Heuristics

- Prefer predictable throughput and bounded memory over clever but opaque micro-optimizations.
- Record benchmark or profiling blockers explicitly when the task is performance-sensitive but measurement is unavailable.
- If the hot path obviously behaves row-by-row on top of Arrow / DataFusion abstractions, flag it as a design risk even if tests pass.
