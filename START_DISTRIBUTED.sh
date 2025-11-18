#!/bin/bash
# Script hướng dẫn khởi động hệ thống ở chế độ DISTRIBUTED (khi ở trường)
# IP Máy 2: 10.38.11.118

echo "=========================================="
echo "🚀 HƯỚNG DẪN KHỞI ĐỘNG HỆ THỐNG DISTRIBUTED"
echo "=========================================="
echo ""
echo "📋 Cấu hình:"
echo "   - Máy 1: Simulator (gửi dữ liệu)"
echo "   - Máy 2: Kafka + Spark + WebSocket (10.38.11.118)"
echo "   - Máy 3: React Frontend (hiển thị)"
echo ""

# Kiểm tra đang ở máy nào
CURRENT_IP=$(hostname -I | awk '{print $1}')
MACHINE2_IP="10.38.11.118"

if [ "$CURRENT_IP" = "$MACHINE2_IP" ]; then
    echo "✅ Bạn đang ở MÁY 2 (Kafka + Spark + WebSocket)"
    echo ""
    echo "📝 Các bước khởi động trên MÁY 2:"
    echo ""
    echo "1️⃣  Cập nhật cấu hình Kafka:"
    echo "   cd may2_kafka_spark"
    echo "   ./update_kafka_config.sh"
    echo ""
    echo "2️⃣  Khởi động Kafka:"
    echo "   ./stop_kafka.sh  # (nếu đang chạy)"
    echo "   ./start_kafka.sh"
    echo "   sleep 10"
    echo "   ./create_topics.sh"
    echo ""
    echo "3️⃣  Khởi động Spark Processor:"
    echo "   bash run_spark_server.sh"
    echo ""
    echo "4️⃣  Khởi động WebSocket Backend:"
    echo "   cd ../may3_visualization_react/backend"
    echo "   source venv/bin/activate  # (nếu có venv)"
    echo "   python3 kafka_websocket_server.py"
    echo ""
elif [ "$CURRENT_IP" != "$MACHINE2_IP" ]; then
    echo "ℹ️  Bạn đang ở máy khác (IP: $CURRENT_IP)"
    echo ""
    
    # Kiểm tra có phải máy 1 không (simulator)
    if [ -d "may1_simulator" ]; then
        echo "📝 Các bước khởi động trên MÁY 1 (Simulator):"
        echo ""
        echo "1️⃣  Khởi động Simulator:"
        echo "   cd may1_simulator"
        echo "   python3 parking_simulator.py --kafka-bootstrap 10.38.11.118:9092"
        echo ""
    fi
    
    # Kiểm tra có phải máy 3 không (frontend)
    if [ -d "may3_visualization_react" ]; then
        echo "📝 Các bước khởi động trên MÁY 3 (Frontend):"
        echo ""
        echo "1️⃣  Chuyển sang distributed mode:"
        echo "   cd may3_visualization_react"
        echo "   ./switch_config.sh"
        echo "   (Chọn 'yes' để chuyển sang distributed)"
        echo ""
        echo "2️⃣  Khởi động React Frontend:"
        echo "   cd frontend"
        echo "   npm run dev"
        echo ""
        echo "3️⃣  Mở trình duyệt:"
        echo "   http://localhost:5173"
        echo ""
    fi
fi

echo "=========================================="
echo "📋 TÓM TẮT THỨ TỰ KHỞI ĐỘNG:"
echo "=========================================="
echo ""
echo "1. MÁY 2: Khởi động Kafka + Spark + WebSocket"
echo "2. MÁY 3: Khởi động React Frontend"
echo "3. MÁY 1: Khởi động Simulator"
echo ""
echo "=========================================="
echo "🔍 KIỂM TRA KẾT NỐI:"
echo "=========================================="
echo ""
echo "Từ máy khác, test kết nối đến Máy 2:"
echo "   telnet 10.38.11.118 9092  # Kafka"
echo "   telnet 10.38.11.118 5000  # WebSocket"
echo ""
echo "Kiểm tra Kafka topics:"
echo "   /home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-topics.sh --list --bootstrap-server 10.38.11.118:9092"
echo ""

