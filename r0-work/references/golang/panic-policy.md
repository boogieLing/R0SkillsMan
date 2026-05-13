# Panic Usage Policy (Golang)

## Core Rule

**panic is NOT an error-handling mechanism.**

panic represents a state where the program **cannot continue safely**.

---

## Strict Prohibitions

### 1. Business logic MUST NOT use panic

panic is STRICTLY PROHIBITED in:
- Request handlers
- Service logic
- Domain logic
- Task execution flows

---

### 2. Allowed panic scenarios (EXPLICIT ONLY)

panic is allowed ONLY when:
- In init() during unrecoverable configuration failure
- Program invariants are violated in a way that indicates severe corruption

---

## Design Rationale

- panic bypasses normal control flow
- panic degrades system stability
- panic complicates monitoring and root-cause analysis
