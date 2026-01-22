"""API endpoints for matrix operations."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies.cognitive_map_dependencies import get_cognitive_map_store
from app.storage.cognitive_map_store import CognitiveMapStore
from app.services.matrix_service import MatrixService

router = APIRouter(prefix="/matrix", tags=["matrix"])

logger = logging.getLogger("app")


class MatrixCellUpdateRequest(BaseModel):
    source_index: int = Field(..., ge=0, description="Row index (source node)")
    target_index: int = Field(..., ge=0, description="Column index (target node)")
    weight: Optional[float] = Field(
        None, ge=-1.0, le=1.0, description="Weight value, null to delete edge"
    )
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence value"
    )


@router.get("")
async def get_matrix(store: CognitiveMapStore = Depends(get_cognitive_map_store)):
    """
    Returns:
        {
            "nodes_order": List[str],
            "matrix": List[List[Optional[float]]],
            "confidence": List[List[Optional[float]]]
        }
    """
    try:
        cognitive_map = await store.get()
        matrix_data = MatrixService.build_matrix(cognitive_map)
        return matrix_data
    except Exception as e:
        logger.error(f"Failed to build matrix: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cell")
async def update_matrix_cell(
    request: MatrixCellUpdateRequest,
    store: CognitiveMapStore = Depends(get_cognitive_map_store),
):
    """
    This modifies the underlying edges in the cognitive map.
    """
    try:
        cognitive_map = await store.get()

        updated_map = MatrixService.update_cell(
            cognitive_map=cognitive_map,
            source_index=request.source_index,
            target_index=request.target_index,
            weight=request.weight,
            confidence=request.confidence,
        )

        result = await store.put(updated_map)

        return result
    except ValueError as e:
        logger.error(f"Invalid matrix cell update: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update matrix cell: {e}")
        raise HTTPException(status_code=500, detail=str(e))
