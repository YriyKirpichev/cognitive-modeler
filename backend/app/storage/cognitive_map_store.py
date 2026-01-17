import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from app.models.cognitive_map_models import CognitiveMapModel

logger = logging.getLogger("app")


def canonical_bytes(model: CognitiveMapModel) -> bytes:
    payload = model.model_dump(by_alias=True, exclude_none=True)
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_of(model: CognitiveMapModel) -> str:
    return hashlib.sha256(canonical_bytes(model)).hexdigest()


@dataclass
class Snapshot:
    map: CognitiveMapModel
    hash: str


class CognitiveMapStore:
    def __init__(self, path: Path, history_limit: int = 20):
        self.path = path
        self.history_limit = history_limit
        self.lock = asyncio.Lock()

        self.current: CognitiveMapModel = CognitiveMapModel()
        self.current_hash: str = sha256_of(self.current)

        self.undo_stack: List[Snapshot] = []  # oldest -> newest
        self.redo_stack: List[Snapshot] = []  # oldest -> newest

    # ---------- persistence (ONLY current) ----------
    async def load(self) -> None:
        async with self.lock:
            if not self.path.exists():
                self.current = CognitiveMapModel()
                self.current_hash = sha256_of(self.current)
                self.undo_stack.clear()
                self.redo_stack.clear()
                return

            data = json.loads(self.path.read_text(encoding="utf-8"))
            logger.info(f"Cognitive map: {data}")
            self.current = CognitiveMapModel.model_validate(data)
            self.current_hash = sha256_of(self.current)
            self.undo_stack.clear()
            self.redo_stack.clear()

    async def save_to_file(self) -> None:
        async with self.lock:
            payload = self.current.model_dump(by_alias=True, exclude_none=True)
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            os.replace(tmp, self.path)

    # ---------- integrity ----------
    def _validate_integrity(self, m: CognitiveMapModel) -> None:
        ids = [n.id for n in m.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate node ids")
        idset = set(ids)
        for e in m.edges:
            if e.source not in idset or e.target not in idset:
                raise ValueError(
                    f"Edge references unknown node id: {e.source} -> {e.target}"
                )

    # ---------- API ops ----------
    async def get(self) -> CognitiveMapModel:
        async with self.lock:
            return self.current

    async def put(self, new_map: CognitiveMapModel) -> CognitiveMapModel:
        async with self.lock:
            self._validate_integrity(new_map)
            new_hash = sha256_of(new_map)

            if new_hash != self.current_hash:
                if not self.undo_stack or self.undo_stack[-1].hash != self.current_hash:
                    self.undo_stack.append(Snapshot(self.current, self.current_hash))
                    self.undo_stack = self.undo_stack[-self.history_limit :]

                self.current = new_map
                self.current_hash = new_hash

                self.redo_stack.clear()

            return self.current

    async def undo(self) -> CognitiveMapModel:
        async with self.lock:
            if not self.undo_stack:
                return self.current

            # current -> redo
            self.redo_stack.append(Snapshot(self.current, self.current_hash))
            self.redo_stack = self.redo_stack[-self.history_limit :]

            # last from undo -> current
            prev = self.undo_stack.pop()
            self.current = prev.map
            self.current_hash = prev.hash
            return self.current

    async def redo(self) -> CognitiveMapModel:
        async with self.lock:
            if not self.redo_stack:
                return self.current

            # current -> undo
            self.undo_stack.append(Snapshot(self.current, self.current_hash))
            self.undo_stack = self.undo_stack[-self.history_limit :]

            nxt = self.redo_stack.pop()
            self.current = nxt.map
            self.current_hash = nxt.hash
            return self.current

    async def history_info(self):
        async with self.lock:
            return {
                "limit": self.history_limit,
                "undo_count": len(self.undo_stack),
                "redo_count": len(self.redo_stack),
                "current_hash": self.current_hash,
            }
