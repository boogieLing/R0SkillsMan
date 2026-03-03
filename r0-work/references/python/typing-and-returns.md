# Typing and Return Value Policy (Python)

## Core Philosophy

Python code under r0-work MUST behave like **statically typed code**.

Type ambiguity is considered a maintenance risk.

---

## Mandatory Rules

### 1. All public functions MUST have type hints

❌ Prohibited:
<<<
def process(data):
    return data["id"]
>>>

✅ Required:
<<<
from typing import Dict

def process(data: Dict[str, int]) -> int:
    return data["id"]
>>>

---

### 2. Return types MUST be explicit and stable

- A function MUST return exactly one declared type
- Union types are allowed ONLY when semantically necessary

❌ Prohibited:
<<<
def parse(x):
    if x:
        return 1
    return "error"
>>>

✅ Required:
<<<
from typing import Union

def parse(x: bool) -> Union[int, str]:
    if x:
        return 1
    return "error"
>>>

---

### 3. Prefer dataclass / TypedDict over dict

Unstructured dict-based programming is DISCOURAGED.

✅ Preferred:
<<<
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
>>>
