# HƯỚNG DẪN DEPLOY SPARK LÊN SERVER

## ✅ XÁC NHẬN

Code Spark hiện tại **HOÀN TOÀN CÓ THỂ** chạy bằng `spark-submit` trên server vì:
- ✅ Có hàm `main()` và `if __name__ == "__main__"`
- ✅ Sử dụng argparse để nhận arguments
- ✅ Không có hardcode paths (checkpoint có thể config qua argument)
- ✅ Sử dụng Spark Structured Streaming (phù hợp với cluster)

---

## CÁCH CHẠY TRÊN SERVER

### 1. Local Mode (Trên cùng máy với Kafka)

```bash
cd may2_kafka_spark

spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:4.0.1 \
  --master local[*] \
  spark_processor.py \
  --kafka-bootstrap localhost:9092 \
  --input-topic parking-raw-events \
  --output-topic parking-processed-results \
  --checkpoint /tmp/parking-checkpoint
```

### 2. Standalone Cluster Mode

```bash
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:4.0.1 \
  --master spark://<SPARK_MASTER_HOST>:7077 \
  --deploy-mode client \
  --executor-memory 2g \
  --executor-cores 2 \
  --total-executor-cores 4 \
  spark_processor.py \
  --kafka-bootstrap <KAFKA_BROKER_IP>:9092 \
  --input-topic parking-raw-events \
  --output-topic parking-processed-results \
  --checkpoint hdfs://<HDFS_NAMENODE>:9000/parking-checkpoint
```

**Ví dụ cụ thể:**
```bash
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:4.0.1 \
  --master spark://192.168.1.100:7077 \
  --deploy-mode client \
  --executor-memory 2g \
  --executor-cores 2 \
  spark_processor.py \
  --kafka-bootstrap 192.168.1.100:9092 \
  --input-topic parking-raw-events \
  --output-topic parking-processed-results \
  --checkpoint hdfs://192.168.1.100:9000/parking-checkpoint
```

### 3. YARN Cluster Mode

```bash
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:4.0.1 \
  --master yarn \
  --deploy-mode cluster \
  --executor-memory 2g \
  --executor-cores 2 \
  --num-executors 2 \
  spark_processor.py \
  --kafka-bootstrap <KAFKA_BROKER_IP>:9092 \
  --input-topic parking-raw-events \
  --output-topic parking-processed-results \
  --checkpoint hdfs://<HDFS_NAMENODE>:9000/parking-checkpoint
```

### 4. Chạy Background (nohup)

```bash
nohup spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:4.0.1 \
  --master local[*] \
  spark_processor.py \
  --kafka-bootstrap localhost:9092 \
  --input-topic parking-raw-events \
  --output-topic parking-processed-results \
  --checkpoint /tmp/parking-checkpoint \
  > spark_processor.log 2>&1 &

# Lưu PID để có thể kill sau
echo $! > spark_processor.pid
```

---

## CẤU HÌNH QUAN TRỌNG KHI CHẠY TRÊN SERVER

### 1. Checkpoint Location ⚠️ QUAN TRỌNG

**Vấn đề:** 
- Local mode: Có thể dùng `/tmp/parking-checkpoint`
- Cluster mode: **PHẢI** dùng shared storage (HDFS, S3, NFS)

**Giải pháp:**

#### Local Mode:
```bash
--checkpoint /tmp/parking-checkpoint
# hoặc
--checkpoint /opt/spark/checkpoints/parking
```

#### Cluster Mode (Standalone/YARN):
```bash
# HDFS (khuyến nghị)
--checkpoint hdfs://namenode:9000/parking-checkpoint

# S3 (nếu dùng AWS)
--checkpoint s3://bucket-name/parking-checkpoint

# NFS/Shared Storage
--checkpoint /mnt/shared/parking-checkpoint
```

**Lý do:** 
- Trong cluster mode, executors chạy trên nhiều nodes
- Cần shared storage để:
  - Lưu state (stateful processing)
  - Recovery khi restart
  - Đảm bảo consistency giữa các nodes

**Kiểm tra HDFS:**
```bash
# Tạo thư mục checkpoint trên HDFS
hdfs dfs -mkdir -p /parking-checkpoint

# Kiểm tra quyền
hdfs dfs -ls /parking-checkpoint
```

### 2. Kafka Bootstrap Servers

**Vấn đề:** Spark cần kết nối đến Kafka broker

**Giải pháp:**
- Nếu Kafka và Spark trên cùng network: dùng internal IP
- Nếu Kafka trên network khác: cấu hình `advertised.listeners` trong Kafka
- Kiểm tra firewall: port 9092 phải mở

**Kiểm tra kết nối:**
```bash
# Từ Spark node, kiểm tra kết nối đến Kafka
telnet <KAFKA_BROKER_IP> 9092

# Hoặc
nc -zv <KAFKA_BROKER_IP> 9092
```

### 3. Spark Packages (Kafka Connector)

**Vấn đề:** Kafka connector cần được load

**Giải pháp 1: Tự động download (khuyến nghị)**
```bash
--packages org.apache.spark:spark-sql-kafka-0-10_2.12:4.0.1
```

**Giải pháp 2: Copy JAR thủ công**
```bash
# Download JAR
wget https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/4.0.1/spark-sql-kafka-0-10_2.12-4.0.1.jar

# Copy vào Spark jars directory
cp spark-sql-kafka-0-10_2.12-4.0.1.jar $SPARK_HOME/jars/

# Sau đó chạy không cần --packages
spark-submit \
  --master local[*] \
  spark_processor.py \
  ...
```

### 4. Memory và Resources

**Cấu hình đề xuất:**

```bash
# Local mode (single machine)
--executor-memory 2g
--executor-cores 2

# Cluster mode (production)
--executor-memory 4g
--executor-cores 4
--num-executors 3
--driver-memory 2g
```

### 5. Dependencies (Pandas)

**Lưu ý:** 
- Pandas đã được Spark tự động include khi dùng `transformWithStateInPandas`
- Không cần cài thêm nếu dùng Spark 4.0.1
- Code không cần pandas trong requirements.txt vì Spark tự quản lý

---

## SCRIPT CHẠY TRÊN SERVER

Tạo file `run_spark_server.sh`:

```bash
#!/bin/bash

# Cấu hình
SPARK_MASTER=${SPARK_MASTER:-"local[*]"}
KAFKA_BOOTSTRAP=${KAFKA_BOOTSTRAP:-"localhost:9092"}
CHECKPOINT=${CHECKPOINT:-"/tmp/parking-checkpoint"}
INPUT_TOPIC=${INPUT_TOPIC:-"parking-raw-events"}
OUTPUT_TOPIC=${OUTPUT_TOPIC:-"parking-processed-results"}

# Log file
LOG_FILE="spark_processor_$(date +%Y%m%d_%H%M%S).log"

echo "Starting Spark Processor..."
echo "Spark Master: $SPARK_MASTER"
echo "Kafka Bootstrap: $KAFKA_BOOTSTRAP"
echo "Checkpoint: $CHECKPOINT"
echo "Log file: $LOG_FILE"

spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:4.0.1 \
  --master $SPARK_MASTER \
  --executor-memory 2g \
  --executor-cores 2 \
  spark_processor.py \
  --kafka-bootstrap $KAFKA_BOOTSTRAP \
  --input-topic $INPUT_TOPIC \
  --output-topic $OUTPUT_TOPIC \
  --checkpoint $CHECKPOINT \
  2>&1 | tee $LOG_FILE
```

**Sử dụng:**
```bash
chmod +x run_spark_server.sh

# Chạy với cấu hình mặc định
./run_spark_server.sh

# Chạy với cấu hình tùy chỉnh
SPARK_MASTER="spark://192.168.1.100:7077" \
KAFKA_BOOTSTRAP="192.168.1.100:9092" \
CHECKPOINT="hdfs://192.168.1.100:9000/parking-checkpoint" \
./run_spark_server.sh
```

---

## MONITORING VÀ DEBUGGING

### 1. Spark UI

Sau khi chạy, truy cập Spark UI:
- **Local mode**: http://localhost:4040
- **Standalone**: http://<SPARK_MASTER>:8080
- **YARN**: http://<YARN_RESOURCE_MANAGER>:8088

### 2. Kiểm tra Logs

```bash
# Xem log real-time
tail -f spark_processor.log

# Tìm lỗi
grep -i error spark_processor.log

# Tìm warnings
grep -i warn spark_processor.log
```

### 3. Kiểm tra Streaming Query

Trong Spark UI:
- Tab "Streaming" → Xem streaming queries
- Kiểm tra:
  - Input rate > 0 (đang nhận dữ liệu)
  - Output rate > 0 (đang gửi dữ liệu)
  - Processing time
  - Batch duration

### 4. Kiểm tra Kafka Topics

```bash
# Kiểm tra input topic
kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic parking-raw-events \
  --from-beginning \
  --max-messages 10

# Kiểm tra output topic
kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic parking-processed-results \
  --from-beginning \
  --max-messages 10
```

---

## TROUBLESHOOTING

### Lỗi: Cannot connect to Kafka

**Nguyên nhân:** 
- Kafka broker không chạy
- Firewall chặn port 9092
- Địa chỉ IP sai

**Giải pháp:**
```bash
# Kiểm tra Kafka đang chạy
ps aux | grep kafka

# Kiểm tra port
netstat -tuln | grep 9092

# Kiểm tra kết nối
telnet <KAFKA_IP> 9092
```

### Lỗi: Checkpoint location not accessible

**Nguyên nhân:**
- Thư mục không tồn tại
- Không có quyền ghi
- Trong cluster mode nhưng dùng local path

**Giải pháp:**
```bash
# Local mode: Tạo thư mục và set quyền
mkdir -p /tmp/parking-checkpoint
chmod 777 /tmp/parking-checkpoint

# Cluster mode: Tạo trên HDFS
hdfs dfs -mkdir -p /parking-checkpoint
hdfs dfs -chmod 777 /parking-checkpoint
```

### Lỗi: Package not found

**Nguyên nhân:**
- Không có internet để download package
- Repository không accessible

**Giải pháp:**
- Download JAR thủ công và copy vào `$SPARK_HOME/jars/`
- Hoặc cấu hình Maven repository nội bộ

### Lỗi: Out of memory

**Nguyên nhân:**
- Executor memory quá thấp
- Quá nhiều state được lưu

**Giải pháp:**
```bash
# Tăng executor memory
--executor-memory 4g

# Hoặc giảm số lượng xe đồng thời trong simulator
```

---

## BEST PRACTICES

1. **Luôn dùng checkpoint location trên shared storage** khi chạy cluster
2. **Monitor Spark UI** để theo dõi performance
3. **Log rotation** để tránh log file quá lớn
4. **Health check script** để tự động restart nếu crash
5. **Backup checkpoint** định kỳ (nếu quan trọng)

---

## KẾT LUẬN

✅ **Code Spark hoàn toàn sẵn sàng chạy trên server bằng spark-submit**

**Điểm quan trọng:**
- ✅ Code đã được thiết kế để chạy standalone
- ✅ Checkpoint location có thể config qua argument
- ✅ Không có hardcode paths
- ✅ Phù hợp với cả local và cluster mode

**Chỉ cần:**
1. Đảm bảo checkpoint location phù hợp với mode (local vs cluster)
2. Cấu hình đúng Kafka bootstrap servers
3. Load đúng Spark packages
4. Monitor qua Spark UI

Chúc bạn deploy thành công! 🚀

