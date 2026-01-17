import logging
from pathlib import Path
from fastapi import APIRouter, Depends
from fastapi import HTTPException
from pydantic import BaseModel
from app.dependencies.cognitive_map_dependencies import get_cognitive_map_store
from app.models.cognitive_map_models import CognitiveMapModel
from app.storage.cognitive_map_store import CognitiveMapStore

router = APIRouter(prefix="/project", tags=["project"])

logger = logging.getLogger("app")


class FilePathRequest(BaseModel):
    file_path: str


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


@router.post("/new", response_model=CognitiveMapModel)
async def new_project(
    request: FilePathRequest,
    store: CognitiveMapStore = Depends(get_cognitive_map_store),
):
    try:
        file_path = Path(request.file_path)
        await store.create_new_at_path(file_path)
        return await store.get()
    except Exception as e:
        logger.error(f"Failed to create new project at {request.file_path}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/open", response_model=CognitiveMapModel)
async def open_project(
    request: FilePathRequest,
    store: CognitiveMapStore = Depends(get_cognitive_map_store),
):
    try:
        file_path = Path(request.file_path)
        await store.load_from_path(file_path)
        return await store.get()
    except FileNotFoundError as e:
        logger.error(f"File not found: {request.file_path}")
        raise HTTPException(
            status_code=404, detail=f"File not found: {request.file_path}"
        )
    except ValueError as e:
        logger.error(f"Invalid cognitive map format in {request.file_path}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid file format: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to open project from {request.file_path}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/save-as", response_model=CognitiveMapModel)
async def save_as_project(
    request: FilePathRequest,
    store: CognitiveMapStore = Depends(get_cognitive_map_store),
):
    try:
        file_path = Path(request.file_path)
        await store.save_as(file_path)
        return await store.get()
    except Exception as e:
        logger.error(f"Failed to save project as {request.file_path}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
