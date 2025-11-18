# CÁC BƯỚC SỬA CHỮA ĐÃ THỰC HIỆN

## ✅ ĐÃ SỬA CÁC VẤN ĐỀ

### 1. ✅ Sửa lỗi DataFrame trong StatefulProcessor
- **Vấn đề**: Hàm `handleExpiredTimer()` trả về `pd.DataFrame()` rỗng không có schema
- **Đã sửa**: 
  - Tạo helper function `create_empty_dataframe()` để tạo DataFrame rỗng với đúng schema
  - Tất cả các hàm trả về DataFrame rỗng đều dùng helper function này
  - Đảm bảo DataFrame trong `handleExpiredTimer()` có đúng schema và dtypes

### 2. ✅ Sửa startingOffsets từ "latest" sang "earliest"
- **Vấn đề**: Spark chỉ đọc dữ liệu mới từ thời điểm khởi động, không đọc dữ liệu cũ
- **Đã sửa**: Đổi `startingOffsets` từ `"latest"` sang `"earliest"` để đọc từ đầu topic

---

## 📋 CÁC BƯỚC TIẾP THEO CẦN THỰC HIỆN

### Bước 1: Xóa checkpoint cũ (QUAN TRỌNG!)

Nếu Spark đã chạy trước đó với checkpoint cũ, cần xóa để reset:

```bash
# Trên Máy 2
rm -rf /tmp/parking-checkpoint
```

**Lưu ý**: Chỉ xóa checkpoint nếu bạn muốn reset hoàn toàn. Nếu muốn tiếp tục từ checkpoint cũ, có thể giữ lại nhưng có thể gặp lỗi.

---

### Bước 2: Khởi động lại hệ thống theo thứ tự

#### 2.1. Máy 2: Khởi động Kafka và Spark

```bash
# Trên Máy 2
cd may2_kafka_spark

# 1. Khởi động Kafka (nếu chưa chạy)
./start_kafka.sh

# 2. Tạo topics (nếu chưa có)
./create_topics.sh

# 3. Xóa checkpoint cũ (nếu cần)
rm -rf /tmp/parking-checkpoint

# 4. Chạy Spark Processor
./run_spark_server.sh
```

**Kiểm tra:**
- [ ] Kafka đang chạy (port 9092)
- [ ] Spark đã khởi động thành công
- [ ] Không có lỗi trong log
- [ ] Spark UI có thể truy cập: http://localhost:4040

---

#### 2.2. Máy 3: Khởi động Visualization

```bash
# Trên Máy 3
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

**Kiểm tra:**
- [ ] Trạng thái hiển thị "✅ Đã kết nối"
- [ ] Dashboard hiển thị (có thể chưa có dữ liệu)

---

#### 2.3. Máy 1: Khởi động Simulator

```bash
# Trên Máy 1
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

**Kiểm tra:**
- [ ] Simulator đã khởi động
- [ ] Log hiển thị "Đã kết nối đến Kafka broker"
- [ ] Log hiển thị events đang được gửi

---

### Bước 3: Kiểm tra luồng dữ liệu

#### 3.1. Kiểm tra Kafka Topics

**Trên Máy 2:**

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
- [ ] Topic `parking-raw-events` có messages (JSON từ Simulator)
- [ ] Topic `parking-processed-results` có messages (JSON từ Spark)
- [ ] Format JSON đúng

---

#### 3.2. Kiểm tra Spark UI

Mở trình duyệt: `http://localhost:4040`

**Kiểm tra:**
- [ ] Streaming query đang chạy (trạng thái: "RUNNING")
- [ ] **Input rate > 0** (đang nhận dữ liệu từ Kafka)
- [ ] **Output rate > 0** (đang gửi dữ liệu lên Kafka)
- [ ] Không có lỗi trong "Failed Jobs"
- [ ] Số lượng records processed > 0

---

#### 3.3. Kiểm tra Visualization

**Trên Máy 3:**

- [ ] Dashboard tự động cập nhật
- [ ] Số lượng "Đã đỗ" tăng dần
- [ ] Số lượng "Trống" giảm dần
- [ ] Bản đồ bãi xe có các vị trí chuyển sang màu đỏ (occupied)
- [ ] Bảng chi tiết hiển thị xe đang đỗ
- [ ] Thời gian đỗ và tiền phải trả được cập nhật

---

## 🔍 DEBUG NẾU VẪN CÓ VẤN ĐỀ

### Kiểm tra Log Spark

```bash
# Trên Máy 2
cd may2_kafka_spark/logs
tail -f spark_processor_*.log
```

**Tìm kiếm:**
- Lỗi "Invalid return type" → Đã sửa
- Lỗi kết nối Kafka → Kiểm tra Kafka đang chạy
- Lỗi parse JSON → Kiểm tra format dữ liệu từ Simulator

---

### Kiểm tra Kafka đang chạy

```bash
# Trên Máy 2
netstat -tuln | grep 9092
```

Kết quả mong đợi: Có port 9092 đang lắng nghe

---

### Kiểm tra Topics tồn tại

```bash
# Trên Máy 2
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-topics.sh \
  --list \
  --bootstrap-server localhost:9092
```

Kết quả mong đợi:
- `parking-raw-events`
- `parking-processed-results`

---

### Kiểm tra số lượng messages trong topics

```bash
# Trên Máy 2
# Kiểm tra topic input
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-run-class.sh \
  kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic parking-raw-events

# Kiểm tra topic output
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-run-class.sh \
  kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic parking-processed-results
```

---

## 📝 LƯU Ý QUAN TRỌNG

1. **Thứ tự khởi động**: Máy 2 → Máy 3 → Máy 1
2. **Xóa checkpoint**: Nếu gặp lỗi, thử xóa checkpoint và khởi động lại
3. **startingOffsets**: Đã đổi thành "earliest" để đọc từ đầu topic
4. **Firewall**: Đảm bảo port 9092 mở nếu kết nối từ xa
5. **IP Address**: Kiểm tra IP máy 2 đúng khi cấu hình ở máy 1 và máy 3

---

## ✅ KẾT QUẢ MONG ĐỢI

Sau khi thực hiện các bước trên:

1. ✅ Máy 1 gửi dữ liệu lên `parking-raw-events`
2. ✅ Máy 2 đọc từ `parking-raw-events`, xử lý và gửi lên `parking-processed-results`
3. ✅ Máy 3 đọc từ `parking-processed-results` và hiển thị visualization
4. ✅ Dashboard cập nhật real-time khi có xe vào/ra
5. ✅ Không có lỗi trong log

---

## 🆘 NẾU VẪN GẶP VẤN ĐỀ

1. Kiểm tra log chi tiết ở từng máy
2. Kiểm tra kết nối mạng giữa các máy
3. Kiểm tra Kafka đang chạy và topics đã được tạo
4. Kiểm tra Spark UI để xem có lỗi gì không
5. Thử xóa checkpoint và khởi động lại từ đầu

