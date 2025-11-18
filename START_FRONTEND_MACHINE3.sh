#!/bin/bash
# Script khởi động Frontend trên MÁY 3

echo "=========================================="
echo "🚀 KHỞI ĐỘNG FRONTEND TRÊN MÁY 3"
echo "=========================================="
echo ""

# Kiểm tra Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js không được tìm thấy!"
    echo "   Vui lòng cài đặt Node.js trước"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo ""

# Di chuyển đến thư mục frontend
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/may3_visualization_react/frontend"

# Kiểm tra config
if [ ! -f "public/config.json" ]; then
    echo "⚠️  Chưa có config.json, chuyển sang distributed mode..."
    cd ..
    ./switch_config.sh <<< "yes" > /dev/null 2>&1
    cd frontend
fi

echo "📋 Config hiện tại:"
cat public/config.json | grep -A 2 '"frontend"' | head -3
echo ""

# Kiểm tra dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Cài đặt dependencies..."
    npm install
    echo ""
fi

# Kiểm tra port 5173
if netstat -tuln 2>/dev/null | grep -q ":5173 "; then
    echo "⚠️  Port 5173 đã được sử dụng!"
    echo "   Vui lòng dừng process đang chạy hoặc dùng port khác"
    exit 1
fi

echo "✅ Đã sẵn sàng!"
echo ""
echo "🚀 Khởi động Frontend..."
echo "   URL: http://localhost:5173"
echo "   WebSocket: http://10.38.11.118:5000"
echo ""
echo "📝 Lưu ý:"
echo "   - Frontend sẽ tự động kết nối đến WebSocket backend"
echo "   - Kiểm tra connection status trên giao diện"
echo "   - Nhấn Ctrl+C để dừng"
echo ""

# Khởi động
npm run dev

