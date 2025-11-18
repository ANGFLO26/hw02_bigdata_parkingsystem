#!/bin/bash
# Script dừng Kafka và Zookeeper

KAFKA_HOME=${KAFKA_HOME:-/home/phanvantai/Downloads/kafka_2.13-3.7.0}

echo "=========================================="
echo "Dừng Kafka Broker"
echo "=========================================="

# Dừng Kafka
if [ -f /tmp/kafka_broker.pid ]; then
    KAFKA_PID=$(cat /tmp/kafka_broker.pid)
    if ps -p $KAFKA_PID > /dev/null 2>&1; then
        echo "Dừng Kafka (PID: $KAFKA_PID)..."
        kill $KAFKA_PID
        sleep 3
        echo "✅ Kafka đã dừng"
    else
        echo "Kafka không đang chạy"
    fi
    rm -f /tmp/kafka_broker.pid
else
    echo "Không tìm thấy PID file, thử dừng bằng script..."
    $KAFKA_HOME/bin/kafka-server-stop.sh 2>/dev/null || echo "Kafka đã dừng hoặc không tìm thấy script"
fi

# Dừng Zookeeper
if [ -f /tmp/kafka_zookeeper.pid ]; then
    ZOOKEEPER_PID=$(cat /tmp/kafka_zookeeper.pid)
    if ps -p $ZOOKEEPER_PID > /dev/null 2>&1; then
        echo "Dừng Zookeeper (PID: $ZOOKEEPER_PID)..."
        kill $ZOOKEEPER_PID
        sleep 3
        echo "✅ Zookeeper đã dừng"
    else
        echo "Zookeeper không đang chạy"
    fi
    rm -f /tmp/kafka_zookeeper.pid
else
    echo "Không tìm thấy PID file, thử dừng bằng script..."
    $KAFKA_HOME/bin/zookeeper-server-stop.sh 2>/dev/null || echo "Zookeeper đã dừng hoặc không tìm thấy script"
fi

echo "✅ Hoàn tất"
