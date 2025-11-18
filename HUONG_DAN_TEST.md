# HƯỚNG DẪN TEST SAU KHI SỬA LỖI

## 🎯 MỤC ĐÍCH

Sau khi sửa lỗi `Invalid return type`, cần test để đảm bảo:
1. Spark Processor khởi động thành công
2. Không còn lỗi "Invalid return type"
3. Spark có thể xử lý dữ liệu và ghi vào output topic

---

## ✅ CÁCH 1: TEST CƠ BẢN (Không cần Máy 1)

**Mục đích:** Kiểm tra Spark khởi động thành công, không còn lỗi

### Bước 1: Xóa checkpoint cũ
```bash
cd may2_kafka_spark
rm -rf /tmp/parking-checkpoint
```

### Bước 2: Khởi động Kafka (nếu chưa chạy)
```bash
cd may2_kafka_spark
./start_kafka.sh
```

### Bước 3: Chạy Spark Processor
```bash
cd may2_kafka_spark
./run_spark_server.sh
```

### Kiểm tra:
- ✅ Spark khởi động thành công
- ✅ Log hiển thị: "Spark streaming đã bắt đầu..."
- ✅ Log hiển thị: "Đọc từ topic: parking-raw-events"
- ✅ Log hiển thị: "Ghi vào topic: parking-processed-results"
- ✅ **KHÔNG CÓ** lỗi "Invalid return type"
- ✅ Spark UI có thể truy cập: http://localhost:4040

**Kết quả mong đợi:**
- Spark đang chạy và đợi dữ liệu từ Kafka
- Không có lỗi trong log

---

## ✅ CÁCH 2: TEST ĐẦY ĐỦ (Cần Máy 1)

**Mục đích:** Kiểm tra toàn bộ luồng dữ liệu từ đầu đến cuối

### Thứ tự khởi động:

#### Bước 1: Máy 2 - Khởi động Kafka và Spark

```bash
# Trên Máy 2
cd may2_kafka_spark

# 1. Khởi động Kafka (nếu chưa chạy)
./start_kafka.sh

# 2. Tạo topics (nếu chưa có)
./create_topics.sh

# 3. Xóa checkpoint cũ
rm -rf /tmp/parking-checkpoint

# 4. Chạy Spark Processor
./run_spark_server.sh
```

**Kiểm tra:**
- ✅ Kafka đang chạy (port 9092)
- ✅ Spark đã khởi động thành công
- ✅ Không có lỗi "Invalid return type"
- ✅ Spark UI: http://localhost:4040

---

#### Bước 2: Máy 1 - Chạy Simulator

**Đợi Spark khởi động xong** (khoảng 10-20 giây), sau đó:

```bash
# Trên Máy 1
cd may1_simulator

# Chạy simulator
python parking_simulator.py \
  --kafka-bootstrap <IP_MÁY_2>:9092 \
  --topic parking-raw-events \
  --duration 5 \
  --interval 2.0
```

**Ví dụ:**
```bash
python parking_simulator.py \
  --kafka-bootstrap 10.38.11.118:9092 \
  --topic parking-raw-events \
  --duration 5 \
  --interval 2.0
```

**Kiểm tra:**
- ✅ Simulator đã khởi động
- ✅ Log hiển thị "Đã kết nối đến Kafka broker"
- ✅ Log hiển thị events đang được gửi

---

#### Bước 3: Kiểm tra kết quả

**Trên Máy 2:**

1. **Kiểm tra Spark UI:** http://localhost:4040
   - ✅ Streaming query đang chạy (status: RUNNING)
   - ✅ **Input rate > 0** (đang nhận dữ liệu)
   - ✅ **Output rate > 0** (đang gửi dữ liệu)
   - ✅ Không có lỗi trong "Failed Jobs"

2. **Kiểm tra Kafka topics:**

```bash
# Kiểm tra topic input (có dữ liệu từ Simulator)
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic parking-raw-events \
  --from-beginning \
  --max-messages 5

# Kiểm tra topic output (có dữ liệu từ Spark)
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic parking-processed-results \
  --from-beginning \
  --max-messages 5
```

**Kết quả mong đợi:**
- ✅ Topic `parking-raw-events` có messages (JSON từ Simulator)
- ✅ Topic `parking-processed-results` có messages (JSON từ Spark)
- ✅ Format JSON đúng

3. **Kiểm tra log Spark:**
   - ✅ Không có lỗi "Invalid return type"
   - ✅ Không có lỗi khác
   - ✅ Có log xử lý dữ liệu

---

## 📋 TÓM TẮT

### Để test nhanh (không cần Máy 1):
- Chỉ cần chạy Máy 2
- Kiểm tra Spark khởi động thành công, không có lỗi

### Để test đầy đủ (cần Máy 1):
1. Máy 2: Kafka → Spark Processor
2. Máy 1: Simulator
3. Kiểm tra: Spark UI, Kafka topics, Log

---

## ⚠️ LƯU Ý

1. **Thứ tự quan trọng:** Máy 2 phải khởi động trước Máy 1
2. **Xóa checkpoint:** Nếu gặp lỗi, thử xóa checkpoint và khởi động lại
3. **Kiểm tra kết nối:** Đảm bảo Máy 1 có thể kết nối đến Máy 2 (port 9092)
4. **IP Address:** Kiểm tra IP máy 2 đúng khi cấu hình ở máy 1

---

## 🎯 KẾT QUẢ MONG ĐỢI

Sau khi test:

1. ✅ Spark Processor khởi động thành công
2. ✅ Không có lỗi "Invalid return type"
3. ✅ Spark đọc được dữ liệu từ `parking-raw-events`
4. ✅ Spark xử lý và ghi được vào `parking-processed-results`
5. ✅ Spark UI hiển thị Input rate và Output rate > 0

