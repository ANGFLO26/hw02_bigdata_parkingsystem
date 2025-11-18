# SỬA LỖI SPARK PACKAGE KHÔNG TÌM THẤY

## 🔍 VẤN ĐỀ

Khi chạy Spark Processor, gặp lỗi:
```
module not found: org.apache.spark#spark-sql-kafka-0-10_2.12;4.0.1
```

## ✅ NGUYÊN NHÂN

Spark 4.0.1 **ĐÃ CÓ SẴN** Kafka connector JAR trong thư mục `jars/`:
- `/home/phanvantai/Downloads/spark-4.0.1/jars/spark-sql-kafka-0-10_2.13-4.0.1.jar`

**Vấn đề:**
- Script đang cố tải package `spark-sql-kafka-0-10_2.12:4.0.1` từ Maven
- Package này không tồn tại vì Spark 4.0.1 dùng Scala 2.13, không phải 2.12
- Không cần tải package vì JAR đã có sẵn trong Spark installation

## 🔧 GIẢI PHÁP

**Đã sửa:** Xóa `--packages` khỏi script vì JAR đã có sẵn.

### Cách 1: Dùng script đã sửa (KHUYẾN NGHỊ)

```bash
cd may2_kafka_spark
./run_spark_server.sh
```

Script đã được cập nhật và không còn dùng `--packages`.

### Cách 2: Chạy thủ công không dùng --packages

```bash
cd may2_kafka_spark
spark-submit \
  --master local[*] \
  --executor-memory 2g \
  --executor-cores 2 \
  --conf spark.sql.streaming.checkpointLocation=/tmp/parking-checkpoint \
  spark_processor.py \
  --kafka-bootstrap localhost:9092 \
  --input-topic parking-raw-events \
  --output-topic parking-processed-results \
  --checkpoint /tmp/parking-checkpoint
```

### Cách 3: Nếu muốn dùng --packages (không khuyến nghị)

Nếu vẫn muốn dùng `--packages`, cần dùng version đúng với Scala 2.13:

```bash
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.1 \
  ...
```

**Lưu ý:** Cách này không cần thiết vì JAR đã có sẵn.

## ✅ KIỂM TRA

Sau khi sửa, chạy lại:

```bash
cd may2_kafka_spark
./run_spark_server.sh
```

**Kết quả mong đợi:**
- ✅ Spark khởi động thành công
- ✅ Không có lỗi "module not found"
- ✅ Spark đọc được từ Kafka topic `parking-raw-events`
- ✅ Spark ghi được vào Kafka topic `parking-processed-results`

## 📝 LƯU Ý

1. **Spark 4.0.1** đã include Kafka connector sẵn, không cần tải thêm
2. **Scala version**: Spark 4.0.1 dùng Scala 2.13, không phải 2.12
3. Nếu gặp lỗi tương tự với package khác, kiểm tra xem JAR đã có sẵn trong `$SPARK_HOME/jars/` chưa

## 🔍 KIỂM TRA JAR CÓ SẴN

Để kiểm tra các JAR có sẵn trong Spark:

```bash
ls /home/phanvantai/Downloads/spark-4.0.1/jars/ | grep kafka
```

Kết quả mong đợi:
```
kafka-clients-3.7.0.jar
spark-sql-kafka-0-10_2.13-4.0.1.jar
spark-token-provider-kafka-0-10_2.13-4.0.1.jar
```

