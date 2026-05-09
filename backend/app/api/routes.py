"""
API 路由模块 - 统一管理所有 API 端点
"""
from fastapi import APIRouter

from .agents import router as agents_router
from .tasks import router as tasks_router
from .collaboration import router as collaboration_router
from .monitoring import router as monitoring_router

router = APIRouter()

# 注册各模块路由
router.include_router(agents_router, prefix="/agents", tags=["智能体管理"])
router.include_router(tasks_router, prefix="/tasks", tags=["任务调度"])
router.include_router(collaboration_router, prefix="/collaboration", tags=["协同会话"])
router.include_router(monitoring_router, prefix="/monitoring", tags=["监控指标"])
