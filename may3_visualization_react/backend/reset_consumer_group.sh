#!/bin/bash
# Script reset consumer group để đọc lại từ đầu

KAFKA_HOME=${KAFKA_HOME:-/home/phanvantai/Downloads/kafka_2.13-3.7.0}
BOOTSTRAP_SERVER=${BOOTSTRAP_SERVER:-localhost:9092}
GROUP_ID="parking-visualization-websocket"

echo "=========================================="
echo "🔄 RESET CONSUMER GROUP"
echo "=========================================="
echo "Group ID: $GROUP_ID"
echo "Bootstrap Server: $BOOTSTRAP_SERVER"
echo ""

# Xóa consumer group
echo "Đang xóa consumer group..."
$KAFKA_HOME/bin/kafka-consumer-groups.sh \
    --bootstrap-server $BOOTSTRAP_SERVER \
    --delete \
    --group $GROUP_ID 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Đã xóa consumer group: $GROUP_ID"
else
    echo "⚠️  Consumer group có thể chưa tồn tại hoặc đã bị xóa"
fi

echo ""
echo "📝 Lưu ý:"
echo "   - Sau khi reset, WebSocket backend sẽ đọc lại từ đầu"
echo "   - Cần khởi động lại WebSocket backend để áp dụng"
echo "   - Hoặc đợi consumer tự động reset khi restart"
echo ""

