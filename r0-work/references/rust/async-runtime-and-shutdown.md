# Async Runtime And Shutdown (Rust / r0-work)

## Runtime Rules

- Assume Tokio as the default async runtime unless repository evidence says otherwise.
- Keep the runtime boundary explicit: identify which tasks run on the main runtime, which tasks are background workers, and which work must leave the async executor.
- Use `spawn_blocking` or an equivalent isolated path for blocking filesystem, compression, CPU-heavy parsing, or legacy sync library calls that would otherwise stall request-serving tasks.
- Every spawned task must have a visible ownership path: who starts it, who cancels it, and how failure is surfaced.

## Shutdown And Cancellation

- Design graceful shutdown before adding new long-lived tasks, queues, or streaming loops.
- Make cancellation explicit for background tasks, subscriptions, and operator executors.
- Timeouts, retry loops, and backoff must not outlive the owning request / session / worker lifecycle without a deliberate supervisor boundary.
- If the task touches channels, streams, or background worker pools, review drain behavior during shutdown and partial failure.

## Backpressure

- Do not assume the async runtime absorbs overload automatically.
- Identify where backpressure should happen: inbound requests, internal queues, stream readers, or compute batch scheduling.
- Prefer bounded queues or explicit admission control over “fire-and-forget” background fan-out.

## Error Surface

- Preserve typed error context across async boundaries.
- Do not lose cancellation, timeout, or shutdown reasons inside generic `anyhow`/string-only surfaces unless repository conventions already require it.
