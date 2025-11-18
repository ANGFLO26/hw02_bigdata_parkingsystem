#!/bin/bash
# Script dừng tất cả services trên MÁY 2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🛑 DỪNG TẤT CẢ SERVICES TRÊN MÁY 2"
echo "=========================================="
echo ""

# 1. Dừng WebSocket Backend
echo "1️⃣  Dừng WebSocket Backend..."
pkill -f "kafka_websocket_server.py" && echo "   ✅ Đã dừng WebSocket Backend" || echo "   ℹ️  WebSocket Backend không chạy"
sleep 1

# 2. Dừng Spark Processor
echo "2️⃣  Dừng Spark Processor..."
pkill -f "spark-submit.*spark_processor" && echo "   ✅ Đã dừng Spark Processor" || echo "   ℹ️  Spark Processor không chạy"
sleep 2

# 3. Dừng Kafka
echo "3️⃣  Dừng Kafka..."
./stop_kafka.sh
echo ""

echo "=========================================="
echo "✅ ĐÃ DỪNG TẤT CẢ SERVICES"
echo "=========================================="

