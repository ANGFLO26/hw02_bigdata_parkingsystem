#!/bin/bash
# Script chạy Spark Processor trên server

# Cấu hình mặc định
SPARK_MASTER=${SPARK_MASTER:-"local[*]"}
KAFKA_BOOTSTRAP=${KAFKA_BOOTSTRAP:-"localhost:9092"}
CHECKPOINT=${CHECKPOINT:-"/tmp/parking-checkpoint"}
INPUT_TOPIC=${INPUT_TOPIC:-"parking-raw-events"}
OUTPUT_TOPIC=${OUTPUT_TOPIC:-"parking-processed-results"}

# Log file
LOG_DIR="logs"
mkdir -p $LOG_DIR
LOG_FILE="$LOG_DIR/spark_processor_$(date +%Y%m%d_%H%M%S).log"

echo "=========================================="
echo "Starting Spark Parking Processor"
echo "=========================================="
echo "Spark Master: $SPARK_MASTER"
echo "Kafka Bootstrap: $KAFKA_BOOTSTRAP"
echo "Checkpoint: $CHECKPOINT"
echo "Input Topic: $INPUT_TOPIC"
echo "Output Topic: $OUTPUT_TOPIC"
echo "Log File: $LOG_FILE"
echo "=========================================="

# Kiểm tra file tồn tại
if [ ! -f "spark_processor.py" ]; then
    echo "ERROR: spark_processor.py not found!"
    exit 1
fi

# Chạy Spark submit
# Lưu ý: Spark 4.0.1 đã có sẵn Kafka connector trong thư mục jars
# Không cần --packages vì JAR đã được include sẵn
spark-submit \
  --master $SPARK_MASTER \
  --executor-memory 2g \
  --executor-cores 2 \
  --conf spark.sql.streaming.checkpointLocation=$CHECKPOINT \
  spark_processor.py \
  --kafka-bootstrap $KAFKA_BOOTSTRAP \
  --input-topic $INPUT_TOPIC \
  --output-topic $OUTPUT_TOPIC \
  --checkpoint $CHECKPOINT \
  2>&1 | tee $LOG_FILE

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo "Spark Processor stopped successfully"
else
    echo "Spark Processor stopped with error code: $EXIT_CODE"
    echo "Check log file: $LOG_FILE"
fi

exit $EXIT_CODE

