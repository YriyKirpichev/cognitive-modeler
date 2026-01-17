from typing import Optional
from app.storage.cognitive_map_store import CognitiveMapStore

_cognitive_map_store: Optional[CognitiveMapStore] = None


def get_cognitive_map_store() -> CognitiveMapStore:
    if _cognitive_map_store is None:
        raise RuntimeError("CognitiveMapStore not initialized")
    return _cognitive_map_store


def set_cognitive_map_store(store: CognitiveMapStore):
    global _cognitive_map_store
    _cognitive_map_store = store
