# Compute Operator Guidance (Rust / r0-work)

## Scope

This file applies when the task involves:
- Arrow arrays, schemas, or `RecordBatch`
- DataFusion query plans, expressions, logical / physical operators
- Custom table providers, UDF / UDAF, or operator-style compute services
- Batch / vectorized execution pipelines

## Core Rules

- Treat operator-service work as columnar / batch compute, not as ordinary CRUD business logic.
- Keep memory layout visible: schema, batch width, allocation pressure, cloning, and ownership should be reviewed explicitly.
- Prefer batch-oriented and vectorized reasoning over row-by-row convenience code when the task is on a hot compute path.
- Avoid hidden copies. If cloning `RecordBatch`, arrays, or intermediate buffers is necessary, explain why.

## DataFusion / Arrow Mindset

- Review operator boundaries in terms of input schema, output schema, ordering assumptions, and error semantics.
- For custom operators or functions, specify null handling, type coercion, overflow / precision behavior, and batch-size assumptions.
- Table provider or execution-plan work must state where pushdown, pruning, partitioning, and parallelism expectations live, even if the first implementation is minimal.

## Service Integration

- If compute is exposed as a service, separate transport concerns from compute pipeline concerns.
- Long-running batch execution must have explicit cancellation, timeout, and progress / observability strategy.
- Do not hide Arrow / DataFusion performance risks behind generic repository/service abstractions when the hot path is operator execution.
