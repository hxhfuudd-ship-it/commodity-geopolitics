#!/bin/bash
# GeoInsight 一键部署脚本
# 用法: bash deploy.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  GeoInsight 地缘洞察 · 服务器部署${NC}"
echo -e "${CYAN}========================================${NC}"

# 1. 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker 未安装，正在安装...${NC}"
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
    echo -e "${GREEN}Docker 安装完成${NC}"
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose 不可用，请确认 Docker 版本 >= 20.10${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker 就绪${NC}"

# 2. 构建并启动
echo -e "${CYAN}正在构建并启动服务（首次约5-10分钟）...${NC}"
docker compose -f docker-compose.prod.yml up -d --build

# 3. 等待数据库就绪
echo -e "${CYAN}等待数据库就绪...${NC}"
for i in $(seq 1 30); do
    if docker exec geo_postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 数据库就绪${NC}"
        break
    fi
    [ "$i" -eq 30 ] && echo -e "${RED}数据库启动超时${NC}" && exit 1
    sleep 2
done

# 4. 恢复数据
if [ -f db_backup.dump ]; then
    echo -e "${CYAN}正在恢复数据库...${NC}"
    docker cp db_backup.dump geo_postgres:/tmp/db_backup.dump
    docker exec geo_postgres pg_restore -U postgres -d commodity_geo --no-owner --no-privileges --clean --if-exists /tmp/db_backup.dump 2>/dev/null || true
    docker exec geo_postgres rm /tmp/db_backup.dump
    echo -e "${GREEN}✓ 数据库恢复完成${NC}"
else
    echo -e "${RED}未找到 db_backup.dump，跳过数据恢复${NC}"
fi

# 5. 等后端启动
echo -e "${CYAN}等待后端启动...${NC}"
for i in $(seq 1 30); do
    if curl -sf http://localhost:9180/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端已启动${NC}"
        break
    fi
    [ "$i" -eq 30 ] && echo -e "${RED}后端启动超时，请检查日志: docker logs geo_backend${NC}"
    sleep 3
done

# 获取服务器IP
SERVER_IP=$(curl -s --max-time 3 ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}  访问地址: http://${SERVER_IP}:9180${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}常用命令:${NC}"
echo "  查看状态: docker compose -f docker-compose.prod.yml ps"
echo "  查看日志: docker compose -f docker-compose.prod.yml logs -f"
echo "  停止服务: docker compose -f docker-compose.prod.yml down"
echo "  彻底删除(含数据): docker compose -f docker-compose.prod.yml down -v"
