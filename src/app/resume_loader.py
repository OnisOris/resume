from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml


class ResumeLoader:
    def __init__(self, path: Path):
        self.path = path
        self._cache: Dict[str, Any] | None = None
        self._last_mtime: float | None = None

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        mtime = self.path.stat().st_mtime
        if self._cache is not None and self._last_mtime == mtime:
            return self._cache
        with self.path.open("r", encoding="utf-8") as fh:
            if self.path.suffix.lower() in {".yaml", ".yml"}:
                data = yaml.safe_load(fh) or {}
            else:
                data = json.load(fh)
        self._cache = data
        self._last_mtime = mtime
        return data
