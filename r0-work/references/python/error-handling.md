# Runtime Error Avoidance Policy (Python)

## Core Principle

Python code MUST be written to **fail early, fail explicitly, and fail predictably**.

Unexpected runtime errors are considered **engineering defects**, not normal behavior.

---

## Mandatory Rules

### 1. Explicit validation before use

Inputs MUST be validated before:
- Indexing
- Attribute access
- Type-dependent operations

❌ Prohibited:
<<<
value = data["key"]
>>>

✅ Required:
<<<
if "key" not in data:
    raise ValueError("missing required key: key")

value = data["key"]
>>>

---

### 2. Avoid implicit None propagation

Functions MUST NOT return None implicitly unless explicitly declared.

❌ Prohibited:
<<<
def foo(x):
    if x > 0:
        return x
>>>

✅ Required:
<<<
def foo(x: int) -> int:
    if x <= 0:
        raise ValueError("x must be positive")
    return x
>>>

---

### 3. Catch narrowly, not broadly

❌ Prohibited:
<<<
try:
    do_something()
except Exception:
    pass
>>>

✅ Required:
<<<
try:
    do_something()
except ValueError as err:
    raise RuntimeError("invalid input") from err
>>>
