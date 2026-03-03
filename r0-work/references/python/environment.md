# Python Environment Policy

## Mandatory Environment Constraints

1. Python 3 ONLY
   - Python 2 syntax, semantics, or compatibility code is STRICTLY PROHIBITED

2. Runtime environment MUST assume Conda / Miniconda
   - Dependencies are managed via environment, not ad-hoc imports
   - No reliance on system Python behavior

---

## Prohibited Practices

- Writing code that depends on Python 2 behavior
- Using deprecated Python 2 idioms
- Implicitly assuming system-wide packages exist

---

## Design Rationale

- Ensures consistent runtime behavior
- Avoids undefined behavior across environments
- Aligns with modern Python engineering standards
