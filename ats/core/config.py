import json
from pathlib import Path
from typing import Any, Dict


class Config:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        with open(self.path, "r") as f:
            self.data: Dict[str, Any] = json.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
