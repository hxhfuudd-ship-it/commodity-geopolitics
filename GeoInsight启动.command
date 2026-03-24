#!/bin/bash
# GeoInsight 地缘洞察 — 双击启动
cd "$(dirname "$0")"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

cleanup() {
  echo -e "\n${CYAN}正在关闭服务...${NC}"
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
  wait 2>/dev/null
  echo -e "${GREEN}已关闭${NC}"
  exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   GeoInsight 地缘洞察 · 启动中...${NC}"
echo -e "${CYAN}========================================${NC}"

# Load nvm (needed for double-click context)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# Check Postgres
if ! pg_isready -h localhost -p 5432 -q 2>/dev/null; then
  echo -e "${RED}Postgres 未运行，请先启动 Postgres${NC}"
  echo "按回车键退出..."
  read
  exit 1
fi

# Check Redis
if ! redis-cli ping -h localhost -p 6379 > /dev/null 2>&1; then
  echo -e "${RED}Redis 未运行，请先启动 Redis${NC}"
  echo "按回车键退出..."
  read
  exit 1
fi

echo -e "${GREEN}✓ Postgres 已连接${NC}"
echo -e "${GREEN}✓ Redis 已连接${NC}"

# Start backend
echo -e "${CYAN}启动后端 (port 8000)...${NC}"
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

for i in $(seq 1 15); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端已启动${NC}"
    break
  fi
  [ "$i" -eq 15 ] && echo -e "${RED}后端启动超时，继续启动前端...${NC}"
  sleep 1
done

# Start frontend
echo -e "${CYAN}启动前端 (port 5173)...${NC}"
cd frontend
npm run dev -- --port 5173 &
FRONTEND_PID=$!
cd ..

sleep 2

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   启动完成！${NC}"
echo -e "${GREEN}   前端: http://localhost:5173${NC}"
echo -e "${GREEN}   后端: http://localhost:8000${NC}"
echo -e "${GREEN}========================================${NC}"

# Auto open browser
open http://localhost:5173

echo -e "${CYAN}按 Ctrl+C 停止所有服务${NC}"
echo ""

wait
