# 智能航班调整系统 Makefile
# 使用说明：
#   make dev      - 同时启动前后端开发服务器
#   make frontend - 仅启动前端服务器
#   make backend  - 仅启动后端服务器
#   make install  - 安装所有依赖
#   make clean    - 清理临时文件
#   make stop     - 停止所有服务

.PHONY: dev frontend backend install clean stop help

# 默认目标
help:
	@echo "智能航班调整系统 - 可用命令："
	@echo "  make dev       - 同时启动前后端开发服务器"
	@echo "  make frontend  - 仅启动前端服务器 (localhost:3000)"
	@echo "  make backend   - 仅启动后端服务器 (localhost:8000)"
	@echo "  make install   - 安装所有依赖"
	@echo "  make clean     - 清理临时文件和缓存"
	@echo "  make stop      - 停止所有运行的服务"
	@echo "  make help      - 显示此帮助信息"

# 同时启动前后端（并行执行）
dev:
	@echo "🚀 启动智能航班调整系统..."
	@echo "📝 前端地址: http://localhost:3000"
	@echo "🔧 后端API: http://localhost:8000"
	@echo "📚 API文档: http://localhost:8000/docs"
	@echo ""
	@echo "按 Ctrl+C 停止所有服务"
	@make -j2 frontend backend

# 启动前端开发服务器
frontend:
	@echo "🎨 启动前端开发服务器..."
	cd frontend && npm run dev

# 启动后端开发服务器
backend:
	@echo "⚙️  启动后端API服务器..."
	cd backend && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 安装所有依赖
install:
	@echo "📦 安装项目依赖..."
	@echo "1. 安装Python依赖..."
	cd backend && pip install -r requirements.txt
	@echo "2. 安装前端依赖..."
	cd frontend && npm install
	@echo "✅ 所有依赖安装完成！"

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true
	cd src/frontend && rm -rf .next node_modules/.cache 2>/dev/null || true
	@echo "✅ 清理完成！"

# 停止所有服务（杀死相关进程）
stop:
	@echo "🛑 停止所有服务..."
	@pkill -f "npm run dev" 2>/dev/null || true
	@pkill -f "uvicorn" 2>/dev/null || true
	@pkill -f "next dev" 2>/dev/null || true
	@echo "✅ 所有服务已停止！"

# 检查服务状态
status:
	@echo "📊 检查服务状态..."
	@echo "前端服务 (端口3000):"
	@lsof -i :3000 2>/dev/null | grep LISTEN || echo "  ❌ 前端服务未运行"
	@echo "后端服务 (端口8000):"
	@lsof -i :8000 2>/dev/null | grep LISTEN || echo "  ❌ 后端服务未运行"

# 快速重启
restart: stop
	@sleep 2
	@make dev

# 生产环境构建
build:
	@echo "🏗️  构建生产版本..."
	cd frontend && npm run build
	@echo "✅ 前端构建完成！"