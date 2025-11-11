# CHECKLIST DEMO HỆ THỐNG BÃI ĐỖ XE

## TRƯỚC KHI DEMO

### ✅ Kiểm tra chuẩn bị

#### Máy 2 (Kafka + Spark)
- [ ] Java đã cài đặt (java -version)
- [ ] Kafka đã cài đặt và cấu hình
- [ ] Spark 4.0.1 đã cài đặt
- [ ] Python 3.8+ đã cài đặt
- [ ] Dependencies đã cài: `pip install -r requirements.txt`
- [ ] Kafka broker đã khởi động
- [ ] Topics đã được tạo (`parking-raw-events`, `parking-processed-results`)
- [ ] Firewall port 9092 đã mở (nếu cần kết nối từ xa)
- [ ] Kiểm tra Kafka đang chạy: `netstat -tuln | grep 9092`

#### Máy 1 (Simulator)
- [ ] Python 3.8+ đã cài đặt
- [ ] Dependencies đã cài: `pip install -r requirements.txt`
- [ ] Có thể ping đến Máy 2
- [ ] Biết IP của Máy 2

#### Máy 3 (Visualization)
- [ ] Python 3.8+ đã cài đặt
- [ ] Dependencies đã cài: `pip install -r requirements.txt`
- [ ] Streamlit đã cài: `streamlit --version`
- [ ] Có thể ping đến Máy 2
- [ ] Biết IP của Máy 2
- [ ] Port 8501 chưa bị chiếm (hoặc dùng port khác)

---

## QUY TRÌNH DEMO

### Bước 1: Khởi động Máy 2 (Kafka Broker)

```bash
# Trên Máy 2
cd may2_kafka_spark

# Khởi động Kafka (nếu chưa chạy)
# Với Zookeeper:
bin/zookeeper-server-start.sh config/zookeeper.properties &
bin/kafka-server-start.sh config/server.properties &

# Hoặc với KRaft:
bin/kafka-server-start.sh config/kraft/server.properties &

# Tạo topics
chmod +x create_topics.sh
./create_topics.sh

# Kiểm tra topics đã tạo
bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

**Kiểm tra:**
- [ ] Kafka broker đang chạy
- [ ] Topics `parking-raw-events` và `parking-processed-results` đã được tạo
- [ ] Log không có lỗi

---

### Bước 2: Khởi động Máy 2 (Spark Processing)

```bash
# Trên Máy 2
cd may2_kafka_spark

# Chạy Spark processing
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:4.0.1 \
  --master local[*] \
  spark_processor.py \
  --kafka-bootstrap localhost:9092 \
  --input-topic parking-raw-events \
  --output-topic parking-processed-results \
  --checkpoint /tmp/parking-checkpoint
```

**Kiểm tra:**
- [ ] Spark đã khởi động thành công
- [ ] Không có lỗi trong log
- [ ] Spark UI có thể truy cập: http://localhost:4040
- [ ] Đang đợi dữ liệu từ Kafka (streaming query đang chạy)

**Lưu ý:** Spark sẽ đợi dữ liệu từ Kafka, không có lỗi là bình thường.

---

### Bước 3: Khởi động Máy 3 (Visualization)

```bash
# Trên Máy 3
cd may3_visualization

# Chạy Streamlit
streamlit run visualization.py
```

**Kiểm tra:**
- [ ] Streamlit đã khởi động
- [ ] Trình duyệt tự động mở tại http://localhost:8501
- [ ] Giao diện hiển thị đúng
- [ ] Sidebar có các trường cấu hình

**Cấu hình trong Streamlit:**
1. Mở sidebar (nút góc trên bên trái)
2. Nhập Kafka Bootstrap Servers: `<IP_MÁY_2>:9092`
3. Kiểm tra Kafka Topic: `parking-processed-results`
4. Nhấn nút "🔄 Kết nối/Khởi động lại"
5. Kiểm tra trạng thái: "✅ Đã kết nối"

**Kiểm tra:**
- [ ] Trạng thái kết nối hiển thị "✅ Đã kết nối"
- [ ] Dashboard hiển thị: Tổng số chỗ: 60, Đã đỗ: 0, Trống: 60
- [ ] Bản đồ bãi xe hiển thị tất cả vị trí màu xanh (trống)

---

### Bước 4: Khởi động Máy 1 (Simulator)

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

**Kiểm tra:**
- [ ] Simulator đã khởi động
- [ ] Log hiển thị "Đã kết nối đến Kafka broker"
- [ ] Log hiển thị "Đã khởi tạo 5 xe ban đầu"
- [ ] Log hiển thị "Bắt đầu simulator"
- [ ] Có log gửi events định kỳ

**Quan sát:**
- [ ] Log hiển thị events đang được gửi
- [ ] Số lượng events tăng dần
- [ ] Không có lỗi "Lỗi gửi event lên Kafka"

---

### Bước 5: Kiểm tra luồng dữ liệu

#### Kiểm tra Kafka topics

```bash
# Trên Máy 2 - Kiểm tra topic input
bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic parking-raw-events \
  --from-beginning

# Trên Máy 2 - Kiểm tra topic output
bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic parking-processed-results \
  --from-beginning
```

**Kiểm tra:**
- [ ] Topic `parking-raw-events` có messages từ Simulator
- [ ] Topic `parking-processed-results` có messages từ Spark
- [ ] Format JSON đúng

#### Kiểm tra Spark Processing

- [ ] Spark UI (http://localhost:4040) hiển thị:
  - [ ] Streaming query đang chạy
  - [ ] Input rate > 0 (đang nhận dữ liệu)
  - [ ] Output rate > 0 (đang gửi dữ liệu)
  - [ ] Không có lỗi

#### Kiểm tra Visualization

- [ ] Dashboard tự động cập nhật
- [ ] Số lượng "Đã đỗ" tăng dần
- [ ] Số lượng "Trống" giảm dần
- [ ] Bản đồ bãi xe có các vị trí chuyển sang màu đỏ (occupied)
- [ ] Bảng chi tiết hiển thị xe đang đỗ
- [ ] Thời gian đỗ và tiền phải trả được cập nhật

---

## KIỂM TRA TÍNH NĂNG

### ✅ Tính năng cơ bản

- [ ] **Simulator**: Gửi events lên Kafka thành công
- [ ] **Spark**: Nhận và xử lý events từ Kafka
- [ ] **Spark**: Tính toán tiền đỗ xe đúng (block 10 phút)
- [ ] **Spark**: Gửi kết quả lên Kafka
- [ ] **Visualization**: Nhận dữ liệu từ Kafka
- [ ] **Visualization**: Hiển thị bản đồ bãi xe
- [ ] **Visualization**: Hiển thị thống kê real-time

### ✅ Tính năng nâng cao

- [ ] **Stateful Processing**: Tracking state của từng xe
- [ ] **Timer**: Cập nhật định kỳ thời gian đỗ và tiền
- [ ] **Xử lý trạng thái**: ENTERING → PARKED → MOVING → EXITING
- [ ] **Real-time update**: Dashboard cập nhật tự động
- [ ] **Error handling**: Xử lý lỗi kết nối, dữ liệu null

---

## XỬ LÝ SỰ CỐ

### Simulator không gửi được dữ liệu

**Kiểm tra:**
```bash
# Kiểm tra kết nối đến Máy 2
ping <IP_MÁY_2>

# Kiểm tra Kafka broker
telnet <IP_MÁY_2> 9092
```

**Giải pháp:**
- Kiểm tra firewall
- Kiểm tra địa chỉ IP đúng
- Kiểm tra Kafka broker đã chạy

### Spark không xử lý được

**Kiểm tra:**
- Xem log Spark trong terminal
- Kiểm tra Spark UI: http://localhost:4040
- Kiểm tra Kafka connector đã load chưa

**Giải pháp:**
- Kiểm tra Spark version phải là 4.0.1
- Kiểm tra packages đã được load
- Kiểm tra checkpoint location có quyền ghi

### Visualization không hiển thị

**Kiểm tra:**
- Xem log trong terminal
- Kiểm tra trạng thái kết nối trong sidebar
- Kiểm tra có nhận được messages không

**Giải pháp:**
- Nhấn "Kết nối/Khởi động lại" trong sidebar
- Kiểm tra địa chỉ Kafka đúng
- Kiểm tra topic name đúng
- Xem log để biết chi tiết lỗi

---

## DEMO SCRIPT

### Giới thiệu hệ thống

1. **Giới thiệu kiến trúc:**
   - Máy 1: Simulator sinh dữ liệu
   - Máy 2: Kafka Broker + Spark Processing
   - Máy 3: Visualization Dashboard

2. **Giải thích luồng dữ liệu:**
   - Simulator → Kafka (raw events)
   - Kafka → Spark (stateful processing)
   - Spark → Kafka (processed results)
   - Kafka → Visualization (real-time display)

3. **Giải thích tính năng:**
   - Tính tiền theo block 10 phút
   - Tracking state của từng xe
   - Cập nhật real-time
   - Hiển thị bản đồ bãi xe

### Trình diễn

1. **Khởi động các thành phần** (theo thứ tự)
2. **Quan sát dữ liệu**:
   - Log của Simulator
   - Spark UI
   - Visualization Dashboard
3. **Giải thích các sự kiện**:
   - Xe vào (ENTERING)
   - Xe đỗ (PARKED)
   - Cập nhật thời gian đỗ
   - Xe ra (EXITING)

---

## CHECKLIST CUỐI CÙNG

- [ ] Tất cả các máy đã khởi động thành công
- [ ] Dữ liệu đang được gửi từ Simulator
- [ ] Spark đang xử lý dữ liệu
- [ ] Visualization đang hiển thị real-time
- [ ] Không có lỗi trong logs
- [ ] Tính năng hoạt động đúng như mong đợi
- [ ] Sẵn sàng để demo!

---

## LƯU Ý QUAN TRỌNG

1. **Thứ tự khởi động**: Luôn khởi động Máy 2 trước, sau đó Máy 3, cuối cùng Máy 1
2. **Kiểm tra kết nối**: Đảm bảo các máy có thể ping đến nhau
3. **Firewall**: Mở port 9092 trên Máy 2 nếu cần kết nối từ xa
4. **Port conflicts**: Kiểm tra port 8501 (Streamlit) và 9092 (Kafka) không bị chiếm
5. **Checkpoint**: Nếu Spark bị lỗi, có thể xóa checkpoint và chạy lại: `rm -rf /tmp/parking-checkpoint`

---

## THỜI GIAN DEMO

- **Setup**: 5-10 phút
- **Demo**: 10-15 phút
- **Q&A**: 5 phút

**Tổng cộng**: ~30 phút

---

Chúc bạn demo thành công! 🚀

