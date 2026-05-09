# 多智能体协同作业平台 - 快速启动脚本
#!/bin/bash

set -e

echo "========================================"
echo "  多智能体协同作业平台 - 快速启动脚本"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误：Docker 未安装${NC}"
        echo "请先安装 Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}错误：Docker Compose 未安装${NC}"
        echo "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker 和 Docker Compose 已安装${NC}"
}

# 检查配置文件
check_config() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}警告：.env 文件不存在，从 .env.example 复制${NC}"
        cp .env.example .env
        echo -e "${YELLOW}请编辑 .env 文件配置环境变量${NC}"
    else
        echo -e "${GREEN}✓ 配置文件已存在${NC}"
    fi
}

# 启动服务
start_services() {
    echo ""
    echo "正在启动服务..."
    
    # 构建并启动所有服务
    docker-compose up -d --build
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  服务启动成功！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "访问以下地址："
    echo "  - API 文档：http://localhost:8000/docs"
    echo "  - ReDoc:     http://localhost:8000/redoc"
    echo "  - 健康检查：http://localhost:8000/health"
    echo "  - RabbitMQ:  http://localhost:15672 (guest/guest)"
    echo "  - Grafana:   http://localhost:3000 (admin/admin)"
    echo "  - Prometheus: http://localhost:9090"
    echo ""
    echo "查看日志：docker-compose logs -f"
    echo "停止服务：docker-compose down"
}

# 初始化数据库
init_database() {
    echo ""
    echo "等待数据库就绪..."
    sleep 10
    
    echo "执行数据库迁移..."
    # TODO: 运行 Alembic 迁移
    # docker-compose exec backend alembic upgrade head
}

# 主函数
main() {
    check_docker
    check_config
    
    echo ""
    read -p "是否继续启动服务？(y/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_services
        init_database
    else
        echo "已取消启动"
        exit 0
    fi
}

# 执行主函数
main
