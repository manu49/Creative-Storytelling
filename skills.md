# Python 3.8 Compatibility

The backend targets `requires-python = ">=3.8"`. Always follow these rules when writing or editing Python files in `backend/app/`.

## Required typing imports

```python
from typing import List, Dict, Set, Tuple, Optional, Union, AsyncIterator, Callable, Awaitable
```

## Type annotation rules

| Instead of (3.9+/3.10+) | Use (3.8 compat) |
|---|---|
| `list[str]` | `List[str]` |
| `dict[str, int]` | `Dict[str, int]` |
| `tuple[int, str]` | `Tuple[int, str]` |
| `str \| None` | `Optional[str]` |
| `int \| str` | `Union[int, str]` |

## FastAPI response models

```python
from typing import List
from fastapi import APIRouter

@router.get("", response_model=List[MyResponse])
async def list_items():
    pass
```

## Common mistakes

**Missing commas in function signatures**
```python
# Wrong
async def my_func(
    param1: str
    param2: int
) -> None: ...

# Correct
async def my_func(
    param1: str,
    param2: int,
) -> None: ...
```

**Pydantic Settings with extra env vars** — always add `extra = "ignore"` so `NEXT_PUBLIC_*` vars don't break validation:
```python
class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        extra = "ignore"
```

## Verify compatibility

```bash
python3 -c "
import py_compile, glob
for f in glob.glob('app/**/*.py', recursive=True):
    try:
        py_compile.compile(f, doraise=True)
        print(f'OK  {f}')
    except py_compile.PyCompileError as e:
        print(f'ERR {f}: {e}')
"
```
