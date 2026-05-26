# Python 3.8 Compatibility Guide

## Overview

This project maintains **Python 3.8 compatibility** across the entire codebase. This document outlines the compatibility constraints and best practices used throughout the project.

## Why Python 3.8?

- **System Constraint**: The deployment environment has Python 3.8.10 as the default/available Python version
- **Legacy Support**: Many production environments still run Python 3.8
- **Compatibility**: Ensures the project works across a broader range of systems

## Key Python 3.8 Restrictions

### 1. **Generic Type Syntax**

❌ **Not Allowed (Python 3.9+)**
```python
def get_items() -> list[str]:
    return ["a", "b"]

data: dict[str, int] = {"x": 1}
result: tuple[int, str] = (42, "answer")
```

✅ **Required (Python 3.8)**
```python
from typing import List, Dict, Tuple

def get_items() -> List[str]:
    return ["a", "b"]

data: Dict[str, int] = {"x": 1}
result: Tuple[int, str] = (42, "answer")
```

### 2. **Union Type Syntax**

❌ **Not Allowed (Python 3.10+)**
```python
value: str | None = None
result: int | str = 42
```

✅ **Required (Python 3.8)**
```python
from typing import Optional, Union

value: Optional[str] = None
result: Union[int, str] = 42

# Preferred for None: Optional[X] instead of Union[X, None]
```

### 3. **Type Annotations in Function Parameters**

✅ **Correct**
```python
from typing import List, Optional

async def process_data(
    items: List[str],
    filter_val: Optional[str] = None,
) -> List[str]:
    pass
```

### 4. **Response Models in FastAPI**

✅ **Correct**
```python
from typing import List
from fastapi import APIRouter

@router.get("", response_model=List[MyResponse])
async def list_items():
    pass
```

## Common Pitfalls

### Missing Commas in Function Signatures
```python
# ❌ WRONG
async def my_func(
    param1: str
    param2: int
) -> None:

# ✅ CORRECT  
async def my_func(
    param1: str,
    param2: int,
) -> None:
```

### Forgotten Type Imports
```python
# ❌ WRONG - List not imported
def get_items() -> List[str]:
    return []

# ✅ CORRECT
from typing import List

def get_items() -> List[str]:
    return []
```

### Configuration Classes with Extra Fields
```python
# ✅ CORRECT - Allow extra env vars (e.g., NEXT_PUBLIC_*)
class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Critical for multi-env .env files
```

## Type Annotations Checklist

When adding new code, use this checklist:

- [ ] No `list[X]`, `dict[X, Y]`, `tuple[X, Y]` - use `List`, `Dict`, `Tuple` instead
- [ ] No `X | Y` union syntax - use `Union[X, Y]` or `Optional[X]`
- [ ] All necessary types imported from `typing` module
- [ ] Function parameters have commas between them (no missing commas)
- [ ] Optional parameters use `Optional[T]` not `T | None`
- [ ] List return types use `List[T]` not `list[T]`

## Standard Imports for Compatibility

```python
# Always include these when needed
from typing import (
    List,
    Dict, 
    Set,
    Tuple,
    Optional,
    Union,
    AsyncIterator,
    Callable,
    Awaitable,
)

# Async
from typing import AsyncIterator

# Callables
from typing import Callable, Awaitable
```

## Testing Compatibility

To verify Python 3.8 compatibility:

```bash
# Check syntax
python3.8 -m py_compile app/services/llm_service.py

# Or test all files
python3 << 'EOF'
import py_compile
import glob

for filepath in glob.glob('app/**/*.py', recursive=True):
    try:
        py_compile.compile(filepath, doraise=True)
        print(f'✅ {filepath}')
    except py_compile.PyCompileError as e:
        print(f'❌ {filepath}: {e}')
EOF
```

## Migration to Python 3.9+

If the project ever upgrades to Python 3.9+, these syntax forms can be modernized:

- `list[str]` (replaces `List[str]`)
- `dict[str, int]` (replaces `Dict[str, int]`)
- `tuple[int, str]` (replaces `Tuple[int, str]`)
- `str | None` (replaces `Optional[str]`)

Until then, stick to the typing module imports for full Python 3.8 compatibility.

## Related Files

- **Backend**: `/backend/app/` - All Python files use these standards
- **Dependencies**: `/backend/pyproject.toml` - `requires-python = ">=3.8"`
- **Configuration**: `/backend/app/config.py` - Pydantic Settings with extra="ignore"

## Questions?

When in doubt, refer to the Python 3.8 typing module documentation:
https://docs.python.org/3.8/library/typing.html
