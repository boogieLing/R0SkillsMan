# Golang Code Style Guide (r0-work)

## Baseline Standard

All code MUST conform to:
- Google Golang Style Guide
- gofmt formatting rules

---

## Function Design Rules

### 1. Single Responsibility

Each function MUST:
- Do exactly one thing
- Have a clearly defined responsibility

---

### 2. Function size constraints

Recommended:
- < 50 lines per function
- < 3 levels of nesting

Deep nesting MUST be refactored.

---

### 3. Early return is REQUIRED

Error paths MUST return early.

❌ Prohibited:
<<<
if err == nil {
    // long logic
}
>>>

✅ Required:
<<<
if err != nil {
    return err
}
>>>

---

## Naming Rules

- Clear > Short
- Avoid unnecessary abbreviations
- Domain terms MUST be explicit
