from fastapi import APIRouter

from app.api.v1.endpoints import project, matrix, metrics

api_router = APIRouter()

api_router.include_router(project.router)
api_router.include_router(matrix.router)
api_router.include_router(metrics.router)
