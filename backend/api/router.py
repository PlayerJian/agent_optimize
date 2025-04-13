from fastapi import APIRouter
from .search import router as search_router
from .feedback import router as feedback_router
from .knowledge_base import router as kb_router
from .analytics import router as analytics_router
from .settings import router as settings_router

api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(search_router, prefix="/search", tags=["search"])
api_router.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
api_router.include_router(kb_router, prefix="/knowledge-base", tags=["knowledge-base"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])