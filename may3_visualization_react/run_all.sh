#!/bin/bash
# Script chạy cả backend và frontend trên máy 2

echo "🚀 Khởi động Bãi Đỗ Xe Visualization..."
echo ""

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 không được tìm thấy!"
    exit 1
fi

# Kiểm tra Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js không được tìm thấy!"
    exit 1
fi

# Kiểm tra Kafka
if ! nc -z localhost 9092 2>/dev/null; then
    echo "⚠️  Kafka không chạy trên localhost:9092"
    echo "   Vui lòng chạy: cd may2_kafka_spark && ./start_kafka.sh"
    echo ""
fi

# Cài đặt backend dependencies nếu chưa có
if [ ! -d "backend/venv" ]; then
    echo "📦 Cài đặt backend dependencies..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Cài đặt frontend dependencies nếu chưa có
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Cài đặt frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo ""
echo "✅ Đã sẵn sàng!"
echo ""
echo "📋 Hướng dẫn:"
echo "   1. Terminal 1 - Chạy backend:"
echo "      cd may3_visualization_react/backend"
echo "      source venv/bin/activate"
echo "      python3 kafka_websocket_server.py"
echo ""
echo "   2. Terminal 2 - Chạy frontend:"
echo "      cd may3_visualization_react/frontend"
echo "      npm run dev"
echo ""
echo "   3. Mở browser: http://localhost:5173"
echo ""

