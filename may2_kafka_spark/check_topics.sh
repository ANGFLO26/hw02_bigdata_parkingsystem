#!/bin/bash
# Script kiểm tra thông tin các Kafka topics

KAFKA_HOME=${KAFKA_HOME:-/home/phanvantai/Downloads/kafka_2.13-3.7.0}
BOOTSTRAP_SERVER=${BOOTSTRAP_SERVER:-localhost:9092}

echo "=========================================="
echo "📋 KIỂM TRA KAFKA TOPICS"
echo "=========================================="
echo "Bootstrap Server: $BOOTSTRAP_SERVER"
echo ""

# 1. Liệt kê tất cả topics
echo "1️⃣  DANH SÁCH TOPICS:"
echo "----------------------------------------"
$KAFKA_HOME/bin/kafka-topics.sh --list --bootstrap-server $BOOTSTRAP_SERVER | grep -v "^__"
echo ""

# 2. Thông tin chi tiết topic parking-raw-events
echo "2️⃣  THÔNG TIN TOPIC: parking-raw-events"
echo "----------------------------------------"
$KAFKA_HOME/bin/kafka-topics.sh --describe --bootstrap-server $BOOTSTRAP_SERVER --topic parking-raw-events
echo ""

# 3. Thông tin chi tiết topic parking-processed-results
echo "3️⃣  THÔNG TIN TOPIC: parking-processed-results"
echo "----------------------------------------"
$KAFKA_HOME/bin/kafka-topics.sh --describe --bootstrap-server $BOOTSTRAP_SERVER --topic parking-processed-results
echo ""

# 4. Đếm messages (sử dụng consumer groups)
echo "4️⃣  SỐ LƯỢNG MESSAGES (High Water Mark):"
echo "----------------------------------------"

# Topic parking-raw-events
echo "Topic: parking-raw-events"
for partition in 0 1 2; do
    offset=$($KAFKA_HOME/bin/kafka-run-class.sh kafka.tools.GetOffsetShell \
        --broker-list $BOOTSTRAP_SERVER \
        --topic parking-raw-events \
        --partition $partition \
        --time -1 2>/dev/null | awk -F: '{print $3}')
    if [ ! -z "$offset" ]; then
        echo "   Partition $partition: $offset messages"
    else
        echo "   Partition $partition: 0 messages"
    fi
done
echo ""

# Topic parking-processed-results
echo "Topic: parking-processed-results"
for partition in 0 1 2; do
    offset=$($KAFKA_HOME/bin/kafka-run-class.sh kafka.tools.GetOffsetShell \
        --broker-list $BOOTSTRAP_SERVER \
        --topic parking-processed-results \
        --partition $partition \
        --time -1 2>/dev/null | awk -F: '{print $3}')
    if [ ! -z "$offset" ]; then
        echo "   Partition $partition: $offset messages"
    else
        echo "   Partition $partition: 0 messages"
    fi
done
echo ""

# 5. Xem sample messages (nếu có)
echo "5️⃣  SAMPLE MESSAGES (3 messages mới nhất):"
echo "----------------------------------------"
echo ""
echo "📥 Topic: parking-raw-events (Input từ Simulator)"
echo "   (Đang lấy messages...)"
timeout 5 $KAFKA_HOME/bin/kafka-console-consumer.sh \
    --bootstrap-server $BOOTSTRAP_SERVER \
    --topic parking-raw-events \
    --max-messages 3 \
    --from-beginning \
    --timeout-ms 3000 2>/dev/null | head -3 | sed 's/^/   /' || echo "   ⚠️  Không có messages hoặc timeout"
echo ""

echo "📤 Topic: parking-processed-results (Output từ Spark)"
echo "   (Đang lấy messages...)"
timeout 5 $KAFKA_HOME/bin/kafka-console-consumer.sh \
    --bootstrap-server $BOOTSTRAP_SERVER \
    --topic parking-processed-results \
    --max-messages 3 \
    --from-beginning \
    --timeout-ms 3000 2>/dev/null | head -3 | sed 's/^/   /' || echo "   ⚠️  Không có messages hoặc timeout"
echo ""

echo "=========================================="
echo "✅ HOÀN TẤT"
echo "=========================================="
echo ""
echo "💡 Lưu ý:"
echo "   - Nếu không có messages, có thể Simulator chưa chạy"
echo "   - Messages có thể đã bị xóa sau 24h (retention.ms=86400000)"
echo "   - Để xem real-time messages, dùng:"
echo "     $KAFKA_HOME/bin/kafka-console-consumer.sh --bootstrap-server $BOOTSTRAP_SERVER --topic <topic-name>"
echo ""

