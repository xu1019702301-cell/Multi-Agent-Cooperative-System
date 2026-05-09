# 多智能体协同作业平台 - 开发环境快速启动指南

## 前置要求

- Python 3.10+
- Docker & Docker Compose (推荐)
- PostgreSQL 15+ (如不使用 Docker)
- Redis 7+ (如不使用 Docker)
- RabbitMQ 3.12+ (如不使用 Docker)

## 方式一：Docker Compose 启动（推荐）

### 1. 克隆项目
```bash
cd /workspace
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，修改必要配置
```

### 3. 一键启动
```bash
./scripts/start.sh
```

或手动执行：
```bash
docker-compose up -d --build
```

### 4. 访问服务
- API 文档：http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查：http://localhost:8000/health
- RabbitMQ 管理：http://localhost:15672 (guest/guest)
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

### 5. 查看日志
```bash
docker-compose logs -f
```

### 6. 停止服务
```bash
docker-compose down
```

## 方式二：本地开发环境

### 1. 安装依赖
```bash
pip install uv
uv pip install -e ".[dev]"
```

### 2. 启动基础设施（使用 Docker）
```bash
docker-compose up -d postgres redis rabbitmq
```

### 3. 配置环境变量
```bash
cp .env.example .env
# 确保 DATABASE_URL、REDIS_HOST、RABBITMQ_HOST 指向 localhost
```

### 4. 运行数据库迁移
```bash
alembic upgrade head
```

### 5. 启动后端服务
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 启动 Celery Worker
```bash
celery -A backend.app.celery_app worker --loglevel=info
```

### 7. 启动 Celery Beat（定时任务）
```bash
celery -A backend.app.celery_app beat --loglevel=info
```

## 验证安装

### 健康检查
```bash
curl http://localhost:8000/health
```

预期响应：
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 测试 API
```bash
# 获取 API 文档
curl http://localhost:8000/docs

# 注册测试智能体
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent-001",
    "agent_name": "测试智能体",
    "agent_type": "data_analysis",
    "capabilities": ["data_processing", "analysis"],
    "endpoint_url": "http://localhost:9000",
    "auth_token": "test-token"
  }'
```

## 常见问题

### 端口被占用
修改 `.env` 中的 PORT 或其他服务端口。

### 数据库连接失败
确保 PostgreSQL 已启动且 `.env` 中的 DATABASE_URL 正确。

### 依赖安装失败
```bash
pip install --upgrade pip
pip install -e ".[dev]" --no-cache-dir
```

## 下一步

1. 阅读 API 文档：http://localhost:8000/docs
2. 查看示例代码：`backend/app/examples/`
3. 运行测试：`pytest tests/`
