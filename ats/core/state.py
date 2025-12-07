from typing import Any, Dict


class GlobalState:
    """Shared snapshot of ATS system state."""

    def __init__(self):
        self._state: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)
