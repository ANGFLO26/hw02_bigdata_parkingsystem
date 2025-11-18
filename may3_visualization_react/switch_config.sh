#!/bin/bash
# Script chuyển đổi giữa local mode và distributed mode

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONFIG_FILE="config.json"
LOCAL_CONFIG="config.local.json"
DISTRIBUTED_CONFIG="config.distributed.json"

echo "=========================================="
echo "🔄 Chuyển đổi cấu hình"
echo "=========================================="

# Kiểm tra file config tồn tại
if [ ! -f "$LOCAL_CONFIG" ]; then
    echo "❌ Không tìm thấy $LOCAL_CONFIG"
    exit 1
fi

if [ ! -f "$DISTRIBUTED_CONFIG" ]; then
    echo "❌ Không tìm thấy $DISTRIBUTED_CONFIG"
    exit 1
fi

# Đọc mode hiện tại
CURRENT_MODE="unknown"
if [ -f "$CONFIG_FILE" ]; then
    CURRENT_MODE=$(grep -o '"mode"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)
fi

echo "Mode hiện tại: $CURRENT_MODE"
echo ""

# Hỏi user muốn chuyển sang mode nào
if [ "$CURRENT_MODE" = "local" ]; then
    echo "Bạn đang ở LOCAL mode (1 máy)"
    echo "Bạn muốn chuyển sang DISTRIBUTED mode (nhiều máy)?"
    read -p "Nhập 'yes' để chuyển, hoặc Enter để giữ nguyên: " answer
    if [ "$answer" = "yes" ] || [ "$answer" = "y" ]; then
        cp "$DISTRIBUTED_CONFIG" "$CONFIG_FILE"
        echo "✅ Đã chuyển sang DISTRIBUTED mode"
        NEW_MODE="distributed"
    else
        echo "ℹ️  Giữ nguyên LOCAL mode"
        NEW_MODE="local"
    fi
elif [ "$CURRENT_MODE" = "distributed" ]; then
    echo "Bạn đang ở DISTRIBUTED mode (nhiều máy)"
    echo "Bạn muốn chuyển sang LOCAL mode (1 máy)?"
    read -p "Nhập 'yes' để chuyển, hoặc Enter để giữ nguyên: " answer
    if [ "$answer" = "yes" ] || [ "$answer" = "y" ]; then
        cp "$LOCAL_CONFIG" "$CONFIG_FILE"
        echo "✅ Đã chuyển sang LOCAL mode"
        NEW_MODE="local"
    else
        echo "ℹ️  Giữ nguyên DISTRIBUTED mode"
        NEW_MODE="distributed"
    fi
else
    # Chưa có config, hỏi user
    echo "Chưa có cấu hình. Bạn muốn chọn mode nào?"
    echo "1) LOCAL mode (chạy trên 1 máy - localhost)"
    echo "2) DISTRIBUTED mode (chạy trên nhiều máy - khi ở trường)"
    read -p "Chọn (1 hoặc 2): " choice
    case $choice in
        1)
            cp "$LOCAL_CONFIG" "$CONFIG_FILE"
            NEW_MODE="local"
            echo "✅ Đã chọn LOCAL mode"
            ;;
        2)
            cp "$DISTRIBUTED_CONFIG" "$CONFIG_FILE"
            NEW_MODE="distributed"
            echo "✅ Đã chọn DISTRIBUTED mode"
            ;;
        *)
            echo "❌ Lựa chọn không hợp lệ, sử dụng LOCAL mode mặc định"
            cp "$LOCAL_CONFIG" "$CONFIG_FILE"
            NEW_MODE="local"
            ;;
    esac
fi

# Copy config vào frontend/public
if [ -d "frontend/public" ]; then
    cp "$CONFIG_FILE" "frontend/public/config.json"
    echo "✅ Đã copy config vào frontend/public/config.json"
fi

echo ""
echo "=========================================="
echo "📋 Cấu hình hiện tại:"
echo "=========================================="
cat "$CONFIG_FILE" | grep -A 10 '"mode"'
echo ""
echo "⚠️  Lưu ý:"
if [ "$NEW_MODE" = "local" ]; then
    echo "   - Backend sẽ kết nối Kafka tại: localhost:9092"
    echo "   - Frontend sẽ kết nối WebSocket tại: http://localhost:5000"
    echo "   - Tất cả chạy trên 1 máy"
else
    echo "   - Backend sẽ kết nối Kafka tại: 10.38.11.118:9092"
    echo "   - Frontend sẽ kết nối WebSocket tại: http://10.38.11.118:5000"
    echo "   - Cần cập nhật IP trong config.distributed.json nếu khác"
    echo "   - Cần khởi động lại backend và frontend để áp dụng"
fi
echo ""

