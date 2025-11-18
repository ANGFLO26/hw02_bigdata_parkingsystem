# ✅ SETUP MÁY 2 HOÀN TẤT

## Trạng thái hiện tại

### ✅ Đã hoàn thành

1. **Java**: ✅ Đã cài đặt (OpenJDK 17.0.16)
2. **Python**: ✅ Đã cài đặt (Python 3.10.12)
3. **Kafka**: ✅ Đã cài đặt và khởi động thành công
   - Vị trí: `/home/phanvantai/Downloads/kafka_2.13-3.7.0`
   - Port: 9092
   - Zookeeper: Port 2181
4. **Spark**: ✅ Đã cài đặt (Spark 4.0.1)
   - Vị trí: `/home/phanvantai/Downloads/spark-4.0.1`
5. **Python Dependencies**: ✅ Đã cài đặt
   - pyspark==4.0.1
   - kafka-python==2.0.2
6. **Kafka Topics**: ✅ Đã tạo
   - `parking-raw-events` (3 partitions)
   - `parking-processed-results` (3 partitions)

## IP Address

- **IP máy 2**: `10.38.11.118`
- **Kafka Bootstrap**: `10.38.11.118:9092` (cho kết nối từ xa) hoặc `localhost:9092` (cho local)

## Scripts có sẵn

### 1. Khởi động Kafka
```bash
cd may2_kafka_spark
./start_kafka.sh
```

### 2. Dừng Kafka
```bash
cd may2_kafka_spark
./stop_kafka.sh
```

### 3. Tạo Topics
```bash
cd may2_kafka_spark
./create_topics.sh
```

### 4. Chạy Spark Processor
```bash
cd may2_kafka_spark
./run_spark_server.sh
```

Hoặc chạy thủ công:
```bash
cd may2_kafka_spark
# Lưu ý: Spark 4.0.1 đã có sẵn Kafka connector, không cần --packages
spark-submit \
  --master local[*] \
  --executor-memory 2g \
  --executor-cores 2 \
  spark_processor.py \
  --kafka-bootstrap localhost:9092 \
  --input-topic parking-raw-events \
  --output-topic parking-processed-results \
  --checkpoint /tmp/parking-checkpoint
```

## Kiểm tra trạng thái

### Kiểm tra Kafka đang chạy
```bash
netstat -tuln | grep 9092
```

### Kiểm tra Topics
```bash
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

### Kiểm tra messages trong topic
```bash
# Input topic
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic parking-raw-events \
  --from-beginning

# Output topic
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic parking-processed-results \
  --from-beginning
```

## Cấu hình mạng

### Cho phép kết nối từ xa

Nếu các máy khác cần kết nối đến Kafka, cần cấu hình `advertised.listeners`:

1. Chỉnh sửa `/home/phanvantai/Downloads/kafka_2.13-3.7.0/config/server.properties`:
```properties
advertised.listeners=PLAINTEXT://10.38.11.118:9092
```

2. Mở firewall (nếu cần):
```bash
sudo ufw allow 9092/tcp
```

3. Khởi động lại Kafka:
```bash
cd may2_kafka_spark
./stop_kafka.sh
./start_kafka.sh
```

## Thứ tự khởi động hệ thống

1. **Máy 2**: Khởi động Kafka và Spark Processor
   ```bash
   cd may2_kafka_spark
   ./start_kafka.sh
   ./run_spark_server.sh
   ```

2. **Máy 3**: Khởi động Visualization
   ```bash
   cd may3_visualization
   streamlit run visualization.py
   ```
   Cấu hình Kafka Bootstrap: `10.38.11.118:9092`

3. **Máy 1**: Khởi động Simulator
   ```bash
   cd may1_simulator
   python parking_simulator.py --kafka-bootstrap 10.38.11.118:9092
   ```

## Troubleshooting

### Kafka không khởi động
- Kiểm tra port 9092 có bị chiếm không
- Xem log: `/home/phanvantai/Downloads/kafka_2.13-3.7.0/logs/kafka.log`
- Xóa dữ liệu cũ và khởi động lại:
  ```bash
  rm -rf /tmp/zookeeper /tmp/kafka-logs
  ./start_kafka.sh
  ```

### Spark không kết nối được Kafka
- Kiểm tra Kafka đã chạy chưa
- Kiểm tra địa chỉ bootstrap servers đúng chưa
- Kiểm tra topics đã được tạo chưa

### Topics không tạo được
- Đợi Kafka khởi động hoàn toàn (khoảng 20 giây)
- Kiểm tra Zookeeper đã chạy chưa
- Xem log để biết lỗi chi tiết

## Logs

- Kafka log: `/home/phanvantai/Downloads/kafka_2.13-3.7.0/logs/kafka.log`
- Zookeeper log: `/home/phanvantai/Downloads/kafka_2.13-3.7.0/logs/zookeeper.log`
- Spark log: `may2_kafka_spark/logs/spark_processor_*.log`

## Spark UI

Sau khi chạy Spark Processor, có thể truy cập Spark UI tại:
- http://localhost:4040

## Lưu ý quan trọng

1. **Checkpoint location**: Spark cần checkpoint để lưu state. Mặc định: `/tmp/parking-checkpoint`
   - Nếu gặp lỗi, có thể xóa và chạy lại: `rm -rf /tmp/parking-checkpoint`

2. **Thứ tự khởi động**: Luôn khởi động Máy 2 trước, sau đó Máy 3, cuối cùng Máy 1

3. **IP Address**: Nếu IP thay đổi, cần cập nhật `advertised.listeners` trong Kafka config

---

**Setup hoàn tất! Máy 2 đã sẵn sàng để chạy hệ thống.** 🚀

