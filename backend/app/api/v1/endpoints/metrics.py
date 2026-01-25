import logging
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.cognitive_map_dependencies import get_cognitive_map_store
from app.storage.cognitive_map_store import CognitiveMapStore
from app.services.metrics_service import MetricsService, MetricsResponse

router = APIRouter(prefix="/metrics", tags=["metrics"])

logger = logging.getLogger("app")


@router.get("", response_model=MetricsResponse)
async def get_metrics(
    store: CognitiveMapStore = Depends(get_cognitive_map_store),
) -> MetricsResponse:
    try:
        cognitive_map = await store.get()
        metrics_response = MetricsService.calculate_metrics(cognitive_map)
        return metrics_response
    except Exception as e:
        logger.error(f"Failed to calculate metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
