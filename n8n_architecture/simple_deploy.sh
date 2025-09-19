#!/bin/bash

# Hoorii n8n 简化部署脚本 - 使用现有.env配置

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🚀 Hoorii n8n Simple Deploy"
echo "==========================="

# 检查现有.env文件
if [ ! -f "../.env" ]; then
    echo -e "${RED}❌ .env file not found in parent directory${NC}"
    exit 1
fi

ANTHROPIC_KEY=$(grep "^ANTHROPIC_API_KEY=" ../.env | cut -d'=' -f2)
LANGFUSE_PUBLIC_KEY=$(grep "^LANGFUSE_PUBLIC_KEY=" ../.env | cut -d'=' -f2)
LANGFUSE_SECRET_KEY=$(grep "^LANGFUSE_SECRET_KEY=" ../.env | cut -d'=' -f2)

if [ -z "$ANTHROPIC_KEY" ]; then
    echo -e "${RED}❌ ANTHROPIC_API_KEY not found in .env file${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found API keys in .env file${NC}"

# 创建目录
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p ./hoorii-n8n/{data,workflows,credentials,custom-nodes,postgres-data,redis-data}

# 复制文件
echo -e "${YELLOW}📋 Copying files...${NC}"
cp smart_home_api_adapter.js ./hoorii-n8n/
cp *.json ./hoorii-n8n/workflows/ 2>/dev/null || true

# 创建.env文件
echo -e "${YELLOW}🔧 Creating n8n .env file...${NC}"
cat > ./hoorii-n8n/.env << EOF
# n8n Configuration
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=hoorii123
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

# Monitoring
LANGFUSE_PUBLIC_KEY=$LANGFUSE_PUBLIC_KEY
LANGFUSE_SECRET_KEY=$LANGFUSE_SECRET_KEY
EOF

# 创建Docker Compose
echo -e "${YELLOW}🐳 Creating Docker Compose...${NC}"
cat > ./hoorii-n8n/docker-compose.yml << 'EOF'
version: '3.8'

services:
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

  redis:
    image: redis:7-alpine
    container_name: hoorii-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - ./redis-data:/data
    ports:
      - "6379:6379"

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
      - postgres
      - redis
EOF

# 创建数据库初始化脚本
cat > ./hoorii-n8n/init.sql << 'EOF'
-- Hoorii n8n Database Schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

CREATE TABLE IF NOT EXISTS conversations (
    session_id VARCHAR(50) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    context_data JSONB DEFAULT '{}',
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

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

CREATE TABLE IF NOT EXISTS user_memories (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    memory_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    importance INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_users_familiarity ON users(familiarity_score);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_user_device ON device_interactions(user_id, device_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memories_user_type ON user_memories(user_id, memory_type, created_at DESC);

-- 默认数据
INSERT INTO devices (device_id, device_type, name, required_familiarity, current_state) VALUES
('light_living_room', 'light', '客厅灯', 10, '{"state": "off", "brightness": 100}'),
('light_bedroom', 'light', '卧室灯', 10, '{"state": "off", "brightness": 50}'),
('speaker_living_room', 'speaker', '客厅音箱', 20, '{"state": "off", "volume": 50}'),
('tv_living_room', 'tv', '客厅电视', 30, '{"state": "off", "channel": 1}'),
('air_conditioner_living_room', 'air_conditioner', '客厅空调', 40, '{"state": "off", "temperature": 25}'),
('curtain_bedroom', 'curtain', '卧室窗帘', 50, '{"state": "open", "position": 100}')
ON CONFLICT (device_id) DO NOTHING;

INSERT INTO users (user_id, name, familiarity_score, interaction_count) VALUES
('test_user', 'Test User', 30, 10)
ON CONFLICT (user_id) DO NOTHING;
EOF

# 启动服务
echo -e "${YELLOW}🚀 Starting services...${NC}"
cd hoorii-n8n

# 停止现有服务
docker-compose down 2>/dev/null || true

# 启动新服务
docker-compose up -d

echo -e "${YELLOW}⏳ Waiting for services to initialize...${NC}"
sleep 15

# 检查服务状态
echo -e "${YELLOW}📊 Service status:${NC}"
docker-compose ps

# 测试连接
echo -e "${YELLOW}🔍 Testing connections...${NC}"

# 测试PostgreSQL
if docker-compose exec -T postgres pg_isready -U hoorii; then
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
else
    echo -e "${RED}❌ PostgreSQL not ready${NC}"
fi

# 测试Redis
if docker-compose exec -T redis redis-cli ping; then
    echo -e "${GREEN}✅ Redis is ready${NC}"
else
    echo -e "${RED}❌ Redis not ready${NC}"
fi

# 测试n8n
echo -e "${YELLOW}🤖 Testing n8n (may take a moment)...${NC}"
for i in {1..10}; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/healthz | grep -q "200"; then
        echo -e "${GREEN}✅ n8n is accessible at http://localhost:5678${NC}"
        break
    elif [ $i -eq 10 ]; then
        echo -e "${YELLOW}⚠️  n8n may still be starting up. Check manually: http://localhost:5678${NC}"
    else
        echo -e "${YELLOW}⏳ Waiting for n8n... (attempt $i/10)${NC}"
        sleep 3
    fi
done

echo ""
echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo ""
echo "📌 Access Information:"
echo "======================"
echo "n8n UI: http://localhost:5678"
echo "Username: admin"
echo "Password: hoorii123"
echo ""
echo "🛠️  Next Steps:"
echo "1. Open http://localhost:5678 in browser"
echo "2. Login with admin/hoorii123"
echo "3. Import workflows from ./workflows/ folder"
echo "4. Test with chat: '开灯' or '查看设备状态'"
echo ""
echo "🔧 Troubleshooting:"
echo "./debug_services.sh - Run diagnostics"
echo "docker-compose logs -f n8n - View n8n logs"