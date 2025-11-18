#!/bin/bash
# Script khởi động Kafka và Zookeeper

KAFKA_HOME=${KAFKA_HOME:-/home/phanvantai/Downloads/kafka_2.13-3.7.0}
LOG_DIR="$KAFKA_HOME/logs"
mkdir -p $LOG_DIR

echo "=========================================="
echo "Khởi động Kafka Broker"
echo "=========================================="
echo "Kafka Home: $KAFKA_HOME"
echo "Log Directory: $LOG_DIR"
echo "=========================================="

# Kiểm tra Kafka đã chạy chưa
if netstat -tuln | grep -q ":9092 "; then
    echo "⚠️  Kafka đã đang chạy trên port 9092"
    exit 1
fi

# Kiểm tra Zookeeper đã chạy chưa
if netstat -tuln | grep -q ":2181 "; then
    echo "⚠️  Zookeeper đã đang chạy trên port 2181"
else
    echo "Khởi động Zookeeper..."
    cd $KAFKA_HOME
    nohup bin/zookeeper-server-start.sh config/zookeeper.properties > $LOG_DIR/zookeeper.log 2>&1 &
    ZOOKEEPER_PID=$!
    echo "Zookeeper PID: $ZOOKEEPER_PID"
    sleep 5
    echo "✅ Zookeeper đã khởi động"
fi

# Khởi động Kafka
echo "Khởi động Kafka Broker..."
cd $KAFKA_HOME
nohup bin/kafka-server-start.sh config/server.properties > $LOG_DIR/kafka.log 2>&1 &
KAFKA_PID=$!
echo "Kafka PID: $KAFKA_PID"
sleep 5

# Kiểm tra Kafka đã chạy chưa
if netstat -tuln | grep -q ":9092 "; then
    echo "✅ Kafka đã khởi động thành công!"
    echo "Port 9092 đang lắng nghe"
else
    echo "❌ Kafka có thể chưa khởi động thành công"
    echo "Kiểm tra log: $LOG_DIR/kafka.log"
    exit 1
fi

echo ""
echo "Lưu PIDs vào file để có thể dừng sau:"
echo "$ZOOKEEPER_PID" > /tmp/kafka_zookeeper.pid
echo "$KAFKA_PID" > /tmp/kafka_broker.pid
echo ""
echo "Để dừng Kafka, chạy: ./stop_kafka.sh"
