from pathlib import Path
from typing import Union

def resolve_path(base : Union[str, Path], path : Union[str, Path]) -> Path:
    path = Path(path)
    if path.is_absolute:
        return path.resolve
    
    return Path(base).resolve / path

def is_binary_file(path : Union[str, Path]) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
            return f"\x00" in chunk

    except(OSError,IOError):
        return False