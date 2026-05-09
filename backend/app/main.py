"""
多智能体协同作业平台 - FastAPI 主应用入口
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog

from .core.config import get_settings
from .api.routes import router as api_router

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger("INFO"),
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("平台启动中", config={
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    })
    
    # TODO: 初始化数据库连接池
    # TODO: 初始化 Redis 连接
    # TODO: 初始化 RabbitMQ 连接
    # TODO: 启动后台任务（心跳检测、自动调度等）
    
    logger.info("平台启动完成")
    
    yield
    
    # 关闭时执行
    logger.info("平台关闭中")
    
    # TODO: 关闭数据库连接
    # TODO: 关闭 Redis 连接
    # TODO: 关闭 RabbitMQ 连接
    # TODO: 清理资源
    
    logger.info("平台已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## 多智能体协同作业平台

创新采用"分布式协同 + 智能联动"模式，实现多智能体程序的实时信息互通、动态协同作业。

### 核心功能
- **智能体标准化注册接入** - 支持多类型智能体灵活接入、统一管理
- **任务智能动态分配** - 基于强化学习的智能调度算法
- **加密式实时信息互通** - TLS 1.3 + 国密 SM4 双重加密
- **全流程作业状态监控** - 实时追踪任务执行状态
- **成果智能校验反馈** - 自动化闭环校验机制

### 技术优势
- 🚀 高并发：支持千级智能体同时在线
- 🔒 高安全：端到端加密通信
- 📊 可观测：全链路监控与日志追踪
- 🔧 可扩展：模块化设计，易于扩展
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("未捕获的异常", error=str(exc), path=request.url.path)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "服务器内部错误，请稍后重试",
            "detail": str(exc) if settings.DEBUG else None
        }
    )


# 健康检查端点
@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": "2024-01-01T00:00:00Z"  # TODO: 实际时间
    }


# 根路径
@app.get("/", tags=["Root"])
async def root():
    """根路径 - API 文档索引"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "多智能体协同作业平台 API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


# 注册 API 路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if not settings.DEBUG else 1
    )
