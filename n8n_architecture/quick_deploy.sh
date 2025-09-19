#!/bin/bash

# Hoorii n8n 快速部署脚本
# 一键部署高性能AI智能家居助手

set -e

echo "🚀 Hoorii n8n Quick Deploy Script"
echo "================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Docker
check_docker() {
    echo -e "${YELLOW}📦 Checking Docker installation...${NC}"
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
        exit 1
    fi
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker is ready${NC}"
}

# 创建目录结构
setup_directories() {
    echo -e "${YELLOW}📁 Creating directory structure...${NC}"
    mkdir -p ./hoorii-n8n/{data,workflows,credentials,custom-nodes}
    mkdir -p ./hoorii-n8n/postgres-data
    mkdir -p ./hoorii-n8n/redis-data
    echo -e "${GREEN}✅ Directories created${NC}"
}

# 生成环境配置
generate_env() {
    echo -e "${YELLOW}🔧 Generating .env file...${NC}"

    # 检查是否存在现有.env文件
    if [ -f "../.env" ]; then
        echo -e "${GREEN}📄 Found existing .env file, extracting API key...${NC}"
        ANTHROPIC_KEY=$(grep "^ANTHROPIC_API_KEY=" ../.env | cut -d'=' -f2)
        LANGFUSE_PUBLIC_KEY=$(grep "^LANGFUSE_PUBLIC_KEY=" ../.env | cut -d'=' -f2)
        LANGFUSE_SECRET_KEY=$(grep "^LANGFUSE_SECRET_KEY=" ../.env | cut -d'=' -f2)

        if [ -n "$ANTHROPIC_KEY" ]; then
            echo -e "${GREEN}✅ Using existing Anthropic API key${NC}"
        else
            read -p "Enter your Anthropic API Key (required): " ANTHROPIC_KEY
        fi
    else
        read -p "Enter your Anthropic API Key (required): " ANTHROPIC_KEY
    fi

    if [ -z "$ANTHROPIC_KEY" ]; then
        echo -e "${RED}❌ Anthropic API Key is required!${NC}"
        exit 1
    fi

    read -p "Enter n8n admin username (default: admin): " N8N_USER
    N8N_USER=${N8N_USER:-admin}

    read -p "Enter n8n admin password (default: hoorii123): " N8N_PASS
    N8N_PASS=${N8N_PASS:-hoorii123}

    cat > ./hoorii-n8n/.env << EOF
# n8n Configuration
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=$N8N_USER
N8N_BASIC_AUTH_PASSWORD=$N8N_PASS
N8N_HOST=0.0.0.0
N8N_PORT=5678
N8N_PROTOCOL=http
WEBHOOK_URL=http://localhost:5678/
N8N_EDITOR_BASE_URL=http://localhost:5678/

# Database
POSTGRES_USER=hoorii
POSTGRES_PASSWORD=hoorii_secure_pass_2024
POSTGRES_DB=hoorii
DATABASE_URL=postgresql://hoorii:hoorii_secure_pass_2024@postgres:5432/hoorii

# Redis Cache
REDIS_HOST=redis
REDIS_PORT=6379

# AI Configuration
ANTHROPIC_API_KEY=$ANTHROPIC_KEY

# Smart Home API (Mock Mode)
SMART_HOME_MODE=mock
SMART_HOME_API=http://localhost:8123

# Performance Settings
N8N_EXECUTIONS_PROCESS=main
N8N_CONCURRENCY_LIMIT=10
EXECUTIONS_TIMEOUT=10
EXECUTIONS_TIMEOUT_MAX=30

# Monitoring (Optional)
LANGFUSE_PUBLIC_KEY=$LANGFUSE_PUBLIC_KEY
LANGFUSE_SECRET_KEY=$LANGFUSE_SECRET_KEY
EOF

    echo -e "${GREEN}✅ Environment configuration created${NC}"
}

# 创建Docker Compose文件
create_docker_compose() {
    echo -e "${YELLOW}🐳 Creating Docker Compose configuration...${NC}"

    cat > ./hoorii-n8n/docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL数据库
  postgres:
    image: postgres:14-alpine
    container_name: hoorii-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: hoorii-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - ./redis-data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # n8n工作流引擎
  n8n:
    image: n8nio/n8n:latest
    container_name: hoorii-n8n
    restart: unless-stopped
    environment:
      - N8N_BASIC_AUTH_ACTIVE=${N8N_BASIC_AUTH_ACTIVE}
      - N8N_BASIC_AUTH_USER=${N8N_BASIC_AUTH_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_BASIC_AUTH_PASSWORD}
      - N8N_HOST=${N8N_HOST}
      - N8N_PORT=${N8N_PORT}
      - N8N_PROTOCOL=${N8N_PROTOCOL}
      - WEBHOOK_URL=${WEBHOOK_URL}
      - N8N_EDITOR_BASE_URL=${N8N_EDITOR_BASE_URL}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=${POSTGRES_DB}
      - DB_POSTGRESDB_USER=${POSTGRES_USER}
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
      - N8N_EXECUTIONS_PROCESS=${N8N_EXECUTIONS_PROCESS}
      - N8N_CONCURRENCY_LIMIT=${N8N_CONCURRENCY_LIMIT}
      - EXECUTIONS_TIMEOUT=${EXECUTIONS_TIMEOUT}
      - EXECUTIONS_TIMEOUT_MAX=${EXECUTIONS_TIMEOUT_MAX}
      - NODE_ENV=production
    ports:
      - "5678:5678"
    volumes:
      - ./data:/home/node/.n8n
      - ./workflows:/workflows
      - ./custom-nodes:/home/node/.n8n/custom
      - ./smart_home_api_adapter.js:/home/node/smart_home_api_adapter.js
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:5678/healthz || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx反向代理（可选，用于生产环境）
  nginx:
    image: nginx:alpine
    container_name: hoorii-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - n8n
    profiles:
      - production

networks:
  default:
    name: hoorii-network
    driver: bridge
EOF

    echo -e "${GREEN}✅ Docker Compose file created${NC}"
}

# 创建数据库初始化脚本
create_db_init() {
    echo -e "${YELLOW}💾 Creating database initialization script...${NC}"

    cat > ./hoorii-n8n/init.sql << 'EOF'
-- Hoorii n8n Database Schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name VARCHAR(100) NOT NULL,
    familiarity_score INTEGER DEFAULT 0 CHECK (familiarity_score >= 0 AND familiarity_score <= 100),
    interaction_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    preferences JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT true
);

-- 设备表
CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(50) PRIMARY KEY,
    device_type VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    current_state JSONB DEFAULT '{}',
    required_familiarity INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 对话会话表
CREATE TABLE IF NOT EXISTS conversations (
    session_id VARCHAR(50) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    context_data JSONB DEFAULT '{}',
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 设备交互记录表
CREATE TABLE IF NOT EXISTS device_interactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    device_id VARCHAR(50) REFERENCES devices(device_id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    parameters JSONB DEFAULT '{}',
    success BOOLEAN DEFAULT true,
    response_time INTEGER,
    session_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- 用户记忆表
CREATE TABLE IF NOT EXISTS user_memories (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    memory_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    importance INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引优化查询性能
CREATE INDEX idx_users_familiarity ON users(familiarity_score);
CREATE INDEX idx_conversations_user ON conversations(user_id, created_at DESC);
CREATE INDEX idx_interactions_user_device ON device_interactions(user_id, device_id, timestamp DESC);
CREATE INDEX idx_memories_user_type ON user_memories(user_id, memory_type, created_at DESC);

-- 插入默认设备数据
INSERT INTO devices (device_id, device_type, name, required_familiarity, current_state) VALUES
('light_living_room', 'light', '客厅灯', 10, '{"state": "off", "brightness": 100}'),
('light_bedroom', 'light', '卧室灯', 10, '{"state": "off", "brightness": 50}'),
('speaker_living_room', 'speaker', '客厅音箱', 20, '{"state": "off", "volume": 50}'),
('tv_living_room', 'tv', '客厅电视', 30, '{"state": "off", "channel": 1}'),
('air_conditioner_living_room', 'air_conditioner', '客厅空调', 40, '{"state": "off", "temperature": 25}'),
('curtain_bedroom', 'curtain', '卧室窗帘', 50, '{"state": "open", "position": 100}')
ON CONFLICT (device_id) DO NOTHING;

-- 创建默认测试用户
INSERT INTO users (user_id, name, familiarity_score, interaction_count) VALUES
('test_user', 'Test User', 30, 10)
ON CONFLICT (user_id) DO NOTHING;
EOF

    echo -e "${GREEN}✅ Database initialization script created${NC}"
}

# 复制工作流文件
copy_workflows() {
    echo -e "${YELLOW}📋 Copying workflow files...${NC}"

    cp smart_home_api_adapter.js ./hoorii-n8n/
    cp *.json ./hoorii-n8n/workflows/

    echo -e "${GREEN}✅ Workflow files copied${NC}"
}

# 启动服务
start_services() {
    echo -e "${YELLOW}🚀 Starting services...${NC}"

    cd hoorii-n8n
    docker-compose pull
    docker-compose up -d

    echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
    sleep 10

    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}✅ All services are running!${NC}"
    else
        echo -e "${RED}❌ Some services failed to start. Check logs with: docker-compose logs${NC}"
        exit 1
    fi
}

# 导入工作流
import_workflows() {
    echo -e "${YELLOW}📥 Importing workflows...${NC}"
    echo -e "${YELLOW}Please manually import the workflow files from the n8n UI:${NC}"
    echo "1. Open http://localhost:5678"
    echo "2. Login with username: $N8N_USER"
    echo "3. Go to Workflows > Import from File"
    echo "4. Import files from ./workflows/ directory"
}

# 显示访问信息
show_access_info() {
    echo ""
    echo -e "${GREEN}🎉 Hoorii n8n deployment completed successfully!${NC}"
    echo ""
    echo "📌 Access Information:"
    echo "========================"
    echo "n8n UI: http://localhost:5678"
    echo "Username: $N8N_USER"
    echo "Password: $N8N_PASS"
    echo ""
    echo "PostgreSQL: localhost:5432"
    echo "Database: hoorii"
    echo "User: hoorii"
    echo ""
    echo "Redis: localhost:6379"
    echo ""
    echo "📚 Quick Start:"
    echo "1. Access n8n UI and import workflows"
    echo "2. Configure Anthropic credentials in n8n"
    echo "3. Test with the chat interface"
    echo ""
    echo "🛠️ Useful Commands:"
    echo "View logs: cd hoorii-n8n && docker-compose logs -f"
    echo "Stop services: cd hoorii-n8n && docker-compose down"
    echo "Restart services: cd hoorii-n8n && docker-compose restart"
    echo "Clean everything: cd hoorii-n8n && docker-compose down -v"
}

# 主流程
main() {
    echo "Starting Hoorii n8n deployment..."

    check_docker
    setup_directories
    generate_env
    create_docker_compose
    create_db_init
    copy_workflows
    start_services
    show_access_info
    import_workflows
}

# 运行主流程
main