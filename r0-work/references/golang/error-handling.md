# Error Handling Policy (Golang)

## Core Philosophy

In Golang, `error` represents a **single, explicit failure event**.

An error is NOT:
- A status flag
- A reusable container
- A generic failure placeholder

Each error MUST preserve its **original semantic meaning**.

---

## Mandatory Rules

### 1. DO NOT reuse error variables

Each error MUST have an independent variable.

❌ Prohibited:
<<<
err := foo()
err = bar()
return err
>>>

✅ Required:
<<<
fooErr := foo()
if fooErr != nil {
    return fooErr
}

barErr := bar()
if barErr != nil {
    return barErr
}
>>>

---

### 2. Error variable names MUST express failure source

Allowed examples:
- parseErr
- validateErr
- dbErr
- ioErr
- marshalErr

❌ Prohibited:
- err
- e
- tmpErr

---

### 3. Errors MUST NOT be silently wrapped or overwritten

If an error is transformed, the original cause MUST be preserved
using explicit wrapping.

---

## Design Rationale (WHY)

- Prevents semantic loss in complex control flows
- Improves log readability and traceability
- Reduces cognitive load when reviewing failure paths
