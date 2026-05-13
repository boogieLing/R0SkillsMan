# Service Boundaries (Rust / r0-work)

## Applicability

Load this file when the task involves:
- Axum HTTP services
- Tonic gRPC services
- Tower middleware / service composition
- Streaming request / response paths
- Shared application state, connection pools, or background dispatch from request handlers

## Boundary Rules

- Keep transport boundaries thin. Handlers should validate, convert, and delegate; they should not own large compute or orchestration loops.
- Make state ownership explicit. Shared state must have clear synchronization and lifetime rules.
- Prefer typed request / response boundaries over loosely structured maps or ad-hoc payload assembly.
- For streaming interfaces, define chunking, cancellation, timeout, and partial-failure behavior before implementation is considered complete.

## Middleware And Observability

- Middleware must not hide control flow or mutate shared state in surprising ways.
- Instrument request IDs, latency boundaries, error classes, and queue / batch pressure where applicable.
- If tracing or metrics are absent, record that gap as a risk instead of assuming service behavior is observable.

## RPC / HTTP Specific Checks

- For gRPC: review stream lifecycle, deadline handling, and backpressure interactions.
- For HTTP: review request body limits, timeout policy, and resource ownership for long-lived responses.
- For both: blocking work must not remain inside the main service path without explicit isolation.
