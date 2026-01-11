from fastapi import APIRouter

from backend.app.api.v1.endpoints import albums, auth, comparisons, rankings, ratings

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(albums.router)
api_router.include_router(ratings.router)
api_router.include_router(comparisons.router)
api_router.include_router(rankings.router)
