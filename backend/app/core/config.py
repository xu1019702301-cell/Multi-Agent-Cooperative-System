from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """平台配置管理 - 支持环境变量覆盖"""
    
    # 基础配置
    APP_NAME: str = "多智能体协同作业平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/macp_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # RabbitMQ 配置
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 加密配置
    ENCRYPTION_KEY: str = "your-encryption-key-32-bytes-long"
    TLS_VERSION: str = "TLSv1.3"
    USE_CHINESE_CRYPTO: bool = True  # 是否使用国密 SM4
    
    # 智能体配置
    MAX_AGENTS: int = 1000
    AGENT_HEARTBEAT_INTERVAL: int = 30
    AGENT_TIMEOUT: int = 300
    
    # 任务调度配置
    TASK_QUEUE_NAME: str = "agent_tasks"
    MAX_TASK_RETRIES: int = 3
    TASK_RETRY_DELAY: int = 60
    SCHEDULER_ALGORITHM: str = "reinforcement_learning"  # reinforcement_learning, round_robin, weighted
    
    # 监控配置
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # 限流配置
    RATE_LIMIT_PER_SECOND: int = 100
    RATE_LIMIT_BURST: int = 200
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取单例配置对象"""
    return Settings()
