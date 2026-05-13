# Rust Engineering References (r0-work)

Use these references when the primary implementation language is `rust`, or when the task is mainly for Rust backend services, async runtimes, RPC / HTTP boundaries, or Arrow / DataFusion style operator-service work.

## Scope

These documents are **mandatory engineering constraints** for Rust work executed under `r0-work`.

This reference set is intentionally narrow:
- Rust backend services
- Tokio-based async execution
- Axum / Tonic / Tower style service boundaries
- Arrow columnar memory model awareness
- DataFusion style compute / operator / batch execution paths

These documents do **not** cover:
- Frontend Rust
- Embedded Rust
- Blockchain / smart-contract development
- Compiler internals
- Generic systems-programming theory beyond what is needed for backend and operator-service tasks

## Loading Order

1. Always load `async-runtime-and-shutdown.md` first.
2. Load `service-boundaries.md` when the task involves HTTP, gRPC, background workers, streaming, or shared service state.
3. Load `compute-operator.md` when the task involves Arrow, DataFusion, columnar data, query execution, custom operators, UDF/UDAF, or batch processing.
4. Load `validation-and-performance.md` before verification, or earlier if the task is performance-sensitive.

## Non-Negotiable Rules

- Do not treat Rust as “generic backend with stricter syntax”; runtime lifecycle and ownership boundaries must stay explicit.
- Do not hide blocking work inside async request paths without explicit isolation and justification.
- Do not model operator-service work like CRUD-only business logic; columnar / batch / pipeline semantics must be reviewed explicitly.
- Do not add ecosystem sprawl. Prefer Tokio, Axum, Tonic, Arrow, and DataFusion as the default first-pass vocabulary unless repository evidence requires otherwise.
