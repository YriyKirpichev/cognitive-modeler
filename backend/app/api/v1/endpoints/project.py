import logging
from fastapi import APIRouter, Depends
from fastapi import HTTPException
from app.dependencies.cognitive_map_dependencies import get_cognitive_map_store
from app.models.cognitive_map_models import CognitiveMapModel
from app.storage.cognitive_map_store import CognitiveMapStore

router = APIRouter(prefix="/project", tags=["project"])

logger = logging.getLogger("app")


@router.get("/map", response_model=CognitiveMapModel)
async def get_map(store: CognitiveMapStore = Depends(get_cognitive_map_store)):
    return await store.get()


@router.put("/map", response_model=CognitiveMapModel)
async def put_map(
    m: CognitiveMapModel, store: CognitiveMapStore = Depends(get_cognitive_map_store)
):
    try:
        return await store.put(m)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/undo", response_model=CognitiveMapModel)
async def undo(store: CognitiveMapStore = Depends(get_cognitive_map_store)):
    return await store.undo()


@router.post("/redo", response_model=CognitiveMapModel)
async def redo(store: CognitiveMapStore = Depends(get_cognitive_map_store)):
    return await store.redo()


@router.get("/history")
async def history(store: CognitiveMapStore = Depends(get_cognitive_map_store)):
    return await store.history_info()


@router.post("/save-to-file")
async def save(store: CognitiveMapStore = Depends(get_cognitive_map_store)):
    await store.save_to_file()
    return {"ok": True}
