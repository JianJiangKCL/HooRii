#!/bin/bash

# Hoorii n8n 服务调试脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔍 Hoorii n8n Services Debug"
echo "============================"

# 检查Docker服务是否运行
check_docker_status() {
    echo -e "${BLUE}📦 Checking Docker services...${NC}"

    if [ ! -d "./hoorii-n8n" ]; then
        echo -e "${RED}❌ hoorii-n8n directory not found. Please run quick_deploy.sh first.${NC}"
        exit 1
    fi

    cd hoorii-n8n

    # 检查docker-compose文件
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}❌ docker-compose.yml not found${NC}"
        exit 1
    fi

    echo -e "${YELLOW}📋 Service Status:${NC}"
    docker-compose ps
    echo ""
}

# 检查服务健康状态
check_service_health() {
    echo -e "${BLUE}🏥 Checking Service Health...${NC}"

    # 检查PostgreSQL
    echo -e "${YELLOW}🐘 PostgreSQL:${NC}"
    if docker-compose exec -T postgres pg_isready -U hoorii > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL is healthy${NC}"
    else
        echo -e "${RED}❌ PostgreSQL is not ready${NC}"
        echo "Logs:"
        docker-compose logs --tail=10 postgres
    fi

    # 检查Redis
    echo -e "${YELLOW}📦 Redis:${NC}"
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis is healthy${NC}"
    else
        echo -e "${RED}❌ Redis is not ready${NC}"
        echo "Logs:"
        docker-compose logs --tail=10 redis
    fi

    # 检查n8n
    echo -e "${YELLOW}🤖 n8n:${NC}"
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/healthz | grep -q "200"; then
        echo -e "${GREEN}✅ n8n is healthy and accessible${NC}"
    else
        echo -e "${RED}❌ n8n is not accessible${NC}"
        echo "Trying to access n8n..."

        # 检查端口是否开放
        if netstat -tuln | grep -q ":5678"; then
            echo -e "${YELLOW}⚠️  Port 5678 is open, but n8n might be starting up${NC}"
        else
            echo -e "${RED}❌ Port 5678 is not open${NC}"
        fi

        echo "n8n logs:"
        docker-compose logs --tail=20 n8n
    fi
    echo ""
}

# 检查网络连接
check_network() {
    echo -e "${BLUE}🌐 Checking Network Connectivity...${NC}"

    # 检查容器网络
    echo -e "${YELLOW}Docker Network:${NC}"
    docker network ls | grep hoorii

    # 检查端口占用
    echo -e "${YELLOW}Port Usage:${NC}"
    echo "Port 5678 (n8n): $(netstat -tuln | grep :5678 || echo 'Not in use')"
    echo "Port 5432 (PostgreSQL): $(netstat -tuln | grep :5432 || echo 'Not in use')"
    echo "Port 6379 (Redis): $(netstat -tuln | grep :6379 || echo 'Not in use')"
    echo ""
}

# 检查配置文件
check_config() {
    echo -e "${BLUE}⚙️  Checking Configuration...${NC}"

    if [ -f ".env" ]; then
        echo -e "${GREEN}✅ .env file exists${NC}"
        echo -e "${YELLOW}Environment variables:${NC}"
        grep -E "^(N8N_|ANTHROPIC_|DATABASE_|POSTGRES_)" .env | sed 's/=.*/=***/' || true
    else
        echo -e "${RED}❌ .env file not found${NC}"
    fi

    echo ""
}

# 显示有用的命令
show_commands() {
    echo -e "${BLUE}🛠️  Useful Commands:${NC}"
    echo "View all logs: docker-compose logs -f"
    echo "View n8n logs: docker-compose logs -f n8n"
    echo "Restart services: docker-compose restart"
    echo "Stop services: docker-compose down"
    echo "Rebuild services: docker-compose up -d --build"
    echo "Clean restart: docker-compose down -v && docker-compose up -d"
    echo ""

    echo -e "${BLUE}🌐 Access URLs:${NC}"
    echo "n8n UI: http://localhost:5678"
    echo "PostgreSQL: localhost:5432"
    echo "Redis: localhost:6379"
    echo ""
}

# 快速修复建议
suggest_fixes() {
    echo -e "${BLUE}🔧 Quick Fix Suggestions:${NC}"

    # 检查是否有服务未启动
    STOPPED_SERVICES=$(docker-compose ps --services --filter "status=exited" 2>/dev/null || true)
    if [ -n "$STOPPED_SERVICES" ]; then
        echo -e "${YELLOW}⚠️  Some services are stopped. Try:${NC}"
        echo "docker-compose up -d"
    fi

    # 检查磁盘空间
    DISK_USAGE=$(df . | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 90 ]; then
        echo -e "${YELLOW}⚠️  Disk space low ($DISK_USAGE%). Clean up space.${NC}"
    fi

    # 检查内存
    FREE_MEM=$(free -m | awk 'NR==2{print $7}')
    if [ "$FREE_MEM" -lt 500 ]; then
        echo -e "${YELLOW}⚠️  Low free memory (${FREE_MEM}MB). Consider freeing up memory.${NC}"
    fi

    echo ""
}

# 主函数
main() {
    check_docker_status
    check_service_health
    check_network
    check_config
    suggest_fixes
    show_commands

    echo -e "${GREEN}🎉 Debug completed!${NC}"
    echo -e "${YELLOW}💡 If n8n is still not accessible, wait 1-2 minutes for initialization.${NC}"
}

# 运行主函数
main