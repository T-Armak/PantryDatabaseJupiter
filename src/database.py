
from pathlib import Path
import pickle
from typing import Any, Callable


class DatabaseManager:
    def __init__(self, file_path: str | Path, default_factory: Callable[[], Any]):
        self.file_path = Path(file_path)
        self.default_factory = default_factory 
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Any:
        if not self.file_path.exists():
            return self.default_factory()
        with open(self.file_path, "rb") as fh:
            data = pickle.load(fh)
        return data

    def save(self, obj: Any) -> None:
        with open(self.file_path, "wb") as fh:
            pickle.dump(obj, fh)
