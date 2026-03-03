# Module and Entry Design Policy (Python)

## Core Principle

Python code MUST be written as **importable modules**, not disposable scripts.

Execution MUST be driven by explicit function calls.

---

## Mandatory Rules

### 1. Avoid CLI-style script design

❌ Prohibited:
<<<
if __name__ == "__main__":
    run()
>>>

unless explicitly required.

---

### 2. Prefer explicit entry functions

✅ Required:
<<<
def execute_task(config: Config) -> Result:
    ...
>>>

The caller controls execution, not the module itself.

---

## Design Rationale

- Improves testability
- Improves composability
- Avoids hidden execution paths
