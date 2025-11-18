#!/bin/bash
# Script tạo Kafka topics cần thiết

KAFKA_HOME=${KAFKA_HOME:-/home/phanvantai/Downloads/kafka_2.13-3.7.0}
BOOTSTRAP_SERVER=${BOOTSTRAP_SERVER:-localhost:9092}

echo "Tạo Kafka topics..."

# Tạo topic parking-raw-events (input từ Simulator)
$KAFKA_HOME/bin/kafka-topics.sh --create \
  --bootstrap-server $BOOTSTRAP_SERVER \
  --topic parking-raw-events \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=86400000 \
  --if-not-exists

# Tạo topic parking-processed-results (output cho Visualization)
$KAFKA_HOME/bin/kafka-topics.sh --create \
  --bootstrap-server $BOOTSTRAP_SERVER \
  --topic parking-processed-results \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=86400000 \
  --if-not-exists

echo "Đã tạo xong các topics!"
echo "Kiểm tra topics:"
$KAFKA_HOME/bin/kafka-topics.sh --list --bootstrap-server $BOOTSTRAP_SERVER

