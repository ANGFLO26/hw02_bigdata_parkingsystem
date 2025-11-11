# MÁY 2: KAFKA BROKER + SPARK PROCESSING

## Mô tả
Máy này đóng vai trò:
- **Kafka Broker**: Nhận và lưu trữ dữ liệu từ Simulator, cung cấp cho Spark và Visualization
- **Spark Processing**: Xử lý stateful để tính toán tiền đỗ xe và tracking trạng thái

## Yêu cầu hệ thống
- Java 8 hoặc 11
- Apache Kafka 2.8+ hoặc 3.x
- Apache Spark 4.0.1
- Python 3.8+ (cho Spark)
- Tối thiểu 4GB RAM

## PHẦN A: CÀI ĐẶT KAFKA BROKER

### 1. Tải và cài đặt Kafka
```bash
# Tải Kafka (ví dụ version 2.13-3.5.0)
wget https://downloads.apache.org/kafka/3.5.0/kafka_2.13-3.5.0.tgz
tar -xzf kafka_2.13-3.5.0.tgz
cd kafka_2.13-3.5.0

# Hoặc với KRaft mode (không cần Zookeeper)
```

### 2. Cấu hình Kafka
Chỉnh sửa file `config/server.properties`:
```properties
# ID của broker (phải unique trong cluster)
broker.id=0

# Địa chỉ lắng nghe
listeners=PLAINTEXT://0.0.0.0:9092

# Thư mục lưu logs
log.dirs=/tmp/kafka-logs

# Zookeeper (nếu dùng)
zookeeper.connect=localhost:2181

# Hoặc KRaft mode
process.roles=broker,controller
node.id=1
controller.quorum.voters=1@localhost:9093
```

### 3. Khởi động Kafka
```bash
# Nếu dùng Zookeeper
bin/zookeeper-server-start.sh config/zookeeper.properties &
bin/kafka-server-start.sh config/server.properties &

# Hoặc KRaft mode
bin/kafka-storage.sh format -t <cluster-id> -c config/kraft/server.properties
bin/kafka-server-start.sh config/kraft/server.properties &
```

### 4. Tạo Kafka Topics
Chạy script tạo topics:
```bash
chmod +x create_topics.sh
./create_topics.sh
```

Hoặc tạo thủ công:
```bash
# Topic input từ Simulator
bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --topic parking-raw-events \
  --partitions 3 \
  --replication-factor 1

# Topic output cho Visualization
bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --topic parking-processed-results \
  --partitions 3 \
  --replication-factor 1
```

### 5. Kiểm tra Kafka đang chạy
```bash
# List topics
bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Xem messages trong topic
bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic parking-raw-events \
  --from-beginning
```

## PHẦN B: CÀI ĐẶT SPARK PROCESSING

### 1. Tải và cài đặt Spark 4.0.1
```bash
# Tải Spark 4.0.1
wget https://archive.apache.org/dist/spark/spark-4.0.1/spark-4.0.1-bin-hadoop3.tgz
tar -xzf spark-4.0.1-bin-hadoop3.tgz
cd spark-4.0.1-bin-hadoop3

# Hoặc tải từ mirror gần nhất
```

### 2. Cài đặt Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Cấu hình Spark
Tạo file `conf/spark-defaults.conf`:
```properties
spark.sql.streaming.stateStore.providerClass=org.apache.spark.sql.execution.streaming.state.HDFSBackedStateStoreProvider
spark.sql.streaming.checkpointLocation=/tmp/parking-checkpoint
spark.sql.streaming.stateStore.maintenanceInterval=60s
```

### 4. Chạy Spark Processing
```bash
# Với cấu hình mặc định
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:4.0.1 \
  spark_processor.py

# Với các tham số tùy chỉnh
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:4.0.1 \
  --master local[*] \
  spark_processor.py \
    --kafka-bootstrap localhost:9092 \
    --input-topic parking-raw-events \
    --output-topic parking-processed-results \
    --checkpoint /tmp/parking-checkpoint
```

## Cấu hình mạng

### Cho phép kết nối từ xa
Nếu các máy khác cần kết nối đến Kafka:

1. Chỉnh sửa `config/server.properties`:
```properties
listeners=PLAINTEXT://0.0.0.0:9092
advertised.listeners=PLAINTEXT://<IP_MÁY_2>:9092
```

2. Mở firewall port 9092:
```bash
sudo ufw allow 9092/tcp
```

## Format dữ liệu

### Input (từ Simulator)
```json
{
  "timestamp": "2024-01-01 10:30:45",
  "timestamp_unix": 1704094245,
  "license_plate": "29A-12345",
  "location": "A1",
  "status_code": "PARKED"
}
```

### Output (cho Visualization)
```json
{
  "timestamp": "2024-01-01 10:30:45",
  "timestamp_unix": 1704094245,
  "license_plate": "29A-12345",
  "location": "A1",
  "status": "PARKED",
  "action": "parking_updated",
  "parked_duration_minutes": 15.5,
  "parked_blocks": 2,
  "total_cost": 20000,
  "event_type": "vehicle_event"
}
```

## Monitoring

### Kafka
```bash
# Xem consumer groups
bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list

# Xem lag của consumer
bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group parking-spark-processor \
  --describe
```

### Spark
- Xem Spark UI: http://localhost:4040
- Xem logs trong terminal hoặc log files

## Troubleshooting

### Kafka không khởi động
- Kiểm tra port 9092 có bị chiếm không: `netstat -tuln | grep 9092`
- Kiểm tra Java đã cài đặt: `java -version`
- Xem logs trong `logs/server.log`

### Spark không kết nối được Kafka
- Kiểm tra Kafka đã chạy chưa
- Kiểm tra địa chỉ bootstrap servers
- Kiểm tra topic đã được tạo chưa

### StatefulProcessor lỗi
- Kiểm tra Spark version phải là 4.0.1
- Kiểm tra checkpoint location có quyền ghi
- Xem logs chi tiết trong Spark UI

## Dừng services

```bash
# Dừng Spark: Ctrl+C trong terminal

# Dừng Kafka
bin/kafka-server-stop.sh

# Dừng Zookeeper (nếu có)
bin/zookeeper-server-stop.sh
```

