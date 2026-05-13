# Logging Coverage Policy (Golang)

## Core Principle

**An error without a log is equivalent to an invisible failure.**

Every failure path MUST be observable.

---

## Mandatory Rules

### 1. Every error return MUST be logged

Before returning any non-nil error:
- A log entry MUST be written
- Logging responsibility is local, not delegated upward

❌ Prohibited:
<<<
if err != nil {
    return err
}
>>>

✅ Required:
<<<
if err != nil {
    logger.Error("failed to load config", "err", err)
    return err
}
>>>

---

### 2. Logs MUST include contextual information

Each error log SHOULD include:
- What failed
- Why it matters
- Key identifiers (ID / params / state)

---

### 3. Log level MUST reflect severity

- Recoverable / expected failure → Warn
- Data corruption / logic violation → Error

---

## Anti-Patterns

- Assuming upper layers will log
- Logging without semantic message
- Logging success paths excessively
