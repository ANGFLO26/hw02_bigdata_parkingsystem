#!/bin/bash
# Script khởi động tất cả services trên MÁY 2 (Kafka + Spark + WebSocket)
# IP Máy 2: 10.38.11.118

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🚀 KHỞI ĐỘNG TẤT CẢ SERVICES TRÊN MÁY 2"
echo "=========================================="
echo "IP Máy 2: 10.38.11.118"
echo ""

# 1. Cập nhật cấu hình Kafka
echo "1️⃣  Cập nhật cấu hình Kafka..."
./update_kafka_config.sh
echo ""

# 2. Dừng Kafka nếu đang chạy
echo "2️⃣  Dừng Kafka (nếu đang chạy)..."
./stop_kafka.sh 2>/dev/null || true
sleep 2
echo ""

# 3. Khởi động Kafka
echo "3️⃣  Khởi động Kafka..."
./start_kafka.sh
if [ $? -ne 0 ]; then
    echo "❌ Lỗi khởi động Kafka!"
    exit 1
fi
echo ""

# 4. Đợi Kafka khởi động hoàn toàn
echo "⏳ Đợi Kafka khởi động hoàn toàn (15 giây)..."
sleep 15
echo ""

# 5. Tạo topics
echo "4️⃣  Tạo Kafka topics..."
./create_topics.sh
if [ $? -ne 0 ]; then
    echo "⚠️  Có thể topics đã tồn tại, tiếp tục..."
fi
echo ""

# 6. Kiểm tra Kafka đã sẵn sàng
echo "5️⃣  Kiểm tra Kafka..."
if netstat -tuln | grep -q ":9092 "; then
    echo "✅ Kafka đang chạy trên port 9092"
else
    echo "❌ Kafka chưa sẵn sàng!"
    exit 1
fi
echo ""

# 7. Khởi động Spark Processor (background)
echo "6️⃣  Khởi động Spark Processor..."
echo "   (Chạy trong background, log: logs/spark_processor_*.log)"
bash run_spark_server.sh > logs/spark_processor_$(date +%Y%m%d_%H%M%S).log 2>&1 &
SPARK_PID=$!
echo "   Spark Processor PID: $SPARK_PID"
sleep 5
echo ""

# 8. Khởi động WebSocket Backend (background)
echo "7️⃣  Khởi động WebSocket Backend..."
cd ../may3_visualization_react/backend

# Kiểm tra venv
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "   ✅ Đã kích hoạt venv"
fi

# Kiểm tra config
if [ ! -f "../config.json" ]; then
    echo "   ⚠️  Chưa có config.json, chuyển sang distributed mode..."
    cd ..
    ./switch_config.sh <<< "yes" > /dev/null 2>&1
    cd backend
fi

python3 kafka_websocket_server.py > ../logs/websocket_backend.log 2>&1 &
WEBSOCKET_PID=$!
echo "   WebSocket Backend PID: $WEBSOCKET_PID"
cd "$SCRIPT_DIR"
sleep 3
echo ""

# 9. Tóm tắt
echo "=========================================="
echo "✅ ĐÃ KHỞI ĐỘNG TẤT CẢ SERVICES"
echo "=========================================="
echo ""
echo "📋 Services đang chạy:"
echo "   ✅ Kafka: port 9092"
echo "   ✅ Spark Processor: PID $SPARK_PID"
echo "   ✅ WebSocket Backend: PID $WEBSOCKET_PID (port 5000)"
echo ""
echo "📝 Logs:"
KAFKA_HOME=${KAFKA_HOME:-/home/phanvantai/Downloads/kafka_2.13-3.7.0}
echo "   - Kafka: $KAFKA_HOME/logs/kafka.log"
echo "   - Spark: $SCRIPT_DIR/logs/spark_processor_*.log"
echo "   - WebSocket: ../may3_visualization_react/logs/websocket_backend.log"
echo ""
echo "🔍 Kiểm tra:"
echo "   - Kafka topics: /home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-topics.sh --list --bootstrap-server localhost:9092"
echo "   - WebSocket: curl http://localhost:5000"
echo ""
echo "🛑 Để dừng tất cả:"
echo "   ./stop_all_machine2.sh"
echo ""

