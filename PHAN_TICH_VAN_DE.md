# PHÂN TÍCH VẤN ĐỀ - MÁY 3 KHÔNG THỂ VISUALIZATION

## 🔍 TÓM TẮT VẤN ĐỀ

Máy 1 đã gửi dữ liệu lên `parking-raw-events` nhưng máy 3 không thể visualization vì không có dữ liệu trong `parking-processed-results`. Vấn đề nằm ở **MÁY 2 (Spark Processor)**.

---

## 🐛 CÁC VẤN ĐỀ ĐÃ PHÁT HIỆN

### ❌ VẤN ĐỀ 1: Lỗi trong Spark StatefulProcessor

**Lỗi trong log:**
```
pyspark.errors.exceptions.base.PySparkValueError: Invalid return type. 
Please make sure that the UDF returns a pandas.DataFrame when the specified return type is StructType.
```

**Nguyên nhân:**
- Hàm `handleExpiredTimer()` trả về `pd.DataFrame()` (DataFrame rỗng không có schema) ở dòng 334 và 348
- Spark yêu cầu DataFrame phải có đúng schema ngay cả khi rỗng

**Vị trí:** `may2_kafka_spark/spark_processor.py`
- Dòng 334: `return pd.DataFrame()`
- Dòng 348: `return pd.DataFrame()`

---

### ❌ VẤN ĐỀ 2: startingOffsets="latest"

**Vấn đề:**
- Spark được cấu hình với `startingOffsets="latest"` (dòng 439)
- Nếu Spark khởi động **SAU** khi máy 1 đã gửi dữ liệu, Spark sẽ **KHÔNG ĐỌC** được dữ liệu cũ
- Spark chỉ đọc dữ liệu mới từ thời điểm khởi động

**Vị trí:** `may2_kafka_spark/spark_processor.py` dòng 439

**Giải pháp:** Đổi thành `"earliest"` để đọc từ đầu topic, hoặc dùng `"latest"` chỉ khi chắc chắn Spark khởi động trước máy 1

---

### ⚠️ VẤN ĐỀ 3: DataFrame trong handleExpiredTimer không đảm bảo schema

**Vấn đề:**
- Dòng 388: `return pd.DataFrame([output_row])` có thể không có đúng dtypes
- Cần đảm bảo DataFrame có đúng schema như `handleInputRows`

---

## 🔧 CÁC BƯỚC SỬA CHỮA

### Bước 1: Sửa hàm handleExpiredTimer

**Thay đổi:**
1. Tạo helper function để tạo DataFrame rỗng với đúng schema
2. Đảm bảo tất cả DataFrame trả về đều có đúng schema và dtypes

### Bước 2: Sửa startingOffsets

**Thay đổi:**
- Đổi từ `"latest"` sang `"earliest"` để đọc được dữ liệu cũ
- Hoặc thêm tham số để có thể chọn

### Bước 3: Kiểm tra lại

**Sau khi sửa:**
1. Xóa checkpoint cũ (nếu có)
2. Khởi động lại Spark processor
3. Kiểm tra log xem có lỗi không
4. Kiểm tra topic `parking-processed-results` có dữ liệu không

---

## 📋 CÁC LỆNH CHẠY CHO TỪNG MÁY

### MÁY 2: Kafka Broker + Spark Processor

#### 1. Khởi động Kafka
```bash
cd may2_kafka_spark
./start_kafka.sh
```

#### 2. Tạo Topics (nếu chưa có)
```bash
cd may2_kafka_spark
./create_topics.sh
```

#### 3. Chạy Spark Processor
```bash
cd may2_kafka_spark

# Xóa checkpoint cũ (nếu cần)
rm -rf /tmp/parking-checkpoint

# Chạy Spark
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

---

### MÁY 1: Simulator

```bash
cd may1_simulator

# Chạy simulator
python parking_simulator.py \
  --kafka-bootstrap <IP_MÁY_2>:9092 \
  --topic parking-raw-events \
  --duration 30 \
  --interval 3.0
```

**Ví dụ:**
```bash
python parking_simulator.py \
  --kafka-bootstrap 10.38.11.118:9092 \
  --topic parking-raw-events \
  --duration 30 \
  --interval 3.0
```

---

### MÁY 3: Visualization

```bash
cd may3_visualization

# Chạy Streamlit
streamlit run visualization.py
```

**Sau đó:**
1. Mở trình duyệt tại `http://localhost:8501`
2. Trong sidebar:
   - **Kafka Bootstrap Servers**: `<IP_MÁY_2>:9092` (ví dụ: `10.38.11.118:9092`)
   - **Kafka Topic**: `parking-processed-results`
3. Nhấn nút **"🔄 Kết nối/Khởi động lại"**

---

## 🔍 KIỂM TRA VÀ DEBUG

### Kiểm tra Kafka Topics có dữ liệu không

**Trên Máy 2:**
```bash
# Kiểm tra topic input
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic parking-raw-events \
  --from-beginning \
  --max-messages 10

# Kiểm tra topic output
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic parking-processed-results \
  --from-beginning \
  --max-messages 10
```

### Kiểm tra Spark UI

Mở trình duyệt: `http://localhost:4040`

Kiểm tra:
- [ ] Streaming query đang chạy
- [ ] Input rate > 0 (đang nhận dữ liệu)
- [ ] Output rate > 0 (đang gửi dữ liệu)
- [ ] Không có lỗi trong "Failed Jobs"

### Kiểm tra Log Spark

```bash
# Xem log mới nhất
cd may2_kafka_spark/logs
tail -f spark_processor_*.log
```

---

## ✅ THỨ TỰ KHỞI ĐỘNG ĐÚNG

1. **Máy 2**: Khởi động Kafka → Tạo topics → Chạy Spark Processor
2. **Máy 3**: Chạy Streamlit → Cấu hình Kafka → Kết nối
3. **Máy 1**: Chạy Simulator

**Lưu ý:** Máy 2 phải khởi động Spark Processor **TRƯỚC** máy 1 để đảm bảo Spark đọc được tất cả dữ liệu (nếu dùng `startingOffsets="latest"`). Hoặc dùng `"earliest"` để đọc từ đầu.

---

## 📝 GHI CHÚ

- Nếu Spark đã chạy với checkpoint cũ, có thể cần xóa checkpoint để reset
- Kiểm tra firewall nếu kết nối từ xa
- Đảm bảo Kafka đang chạy trước khi chạy Spark
- Kiểm tra log để xem lỗi chi tiết

