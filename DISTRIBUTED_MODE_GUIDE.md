# 🚀 HƯỚNG DẪN CHẠY HỆ THỐNG Ở CHẾ ĐỘ DISTRIBUTED

## 📋 Tổng quan

Hệ thống chạy trên **3 máy** khi ở trường:
- **Máy 1**: Simulator (gửi dữ liệu vào Kafka)
- **Máy 2**: Kafka + Spark Processor + WebSocket Backend (IP: **10.38.11.118**)
- **Máy 3**: React Frontend (hiển thị dữ liệu)

---

## 🔧 CẤU HÌNH

### ✅ Đã được cấu hình tự động:
- ✅ Kafka config: `listeners=0.0.0.0:9092`, `advertised.listeners=10.38.11.118:9092`
- ✅ Visualization config: đã chuyển sang distributed mode
- ✅ WebSocket Backend: đọc từ `config.json` → `10.38.11.118:9092`

### 📝 Cần cấu hình thủ công:
- **Máy 1**: Chạy Simulator với `--kafka-bootstrap 10.38.11.118:9092`
- **Máy 3**: Đảm bảo đã chuyển sang distributed mode

---

## 🚀 KHỞI ĐỘNG HỆ THỐNG

### Bước 1: MÁY 2 - Khởi động Kafka + Spark + WebSocket

```bash
cd may2_kafka_spark

# Cách 1: Tự động (khuyến nghị)
./start_all_machine2.sh

# Cách 2: Thủ công
./update_kafka_config.sh    # Cập nhật config
./stop_kafka.sh             # Dừng nếu đang chạy
./start_kafka.sh            # Khởi động Kafka
sleep 15
./create_topics.sh          # Tạo topics

# Khởi động Spark Processor (terminal riêng)
bash run_spark_server.sh

# Khởi động WebSocket Backend (terminal riêng)
cd ../may3_visualization_react/backend
source venv/bin/activate  # Nếu có venv
python3 kafka_websocket_server.py
```

**Kiểm tra:**
```bash
# Kiểm tra Kafka
netstat -tuln | grep 9092
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Kiểm tra WebSocket
curl http://localhost:5000
```

---

### Bước 2: MÁY 3 - Khởi động React Frontend

```bash
cd may3_visualization_react

# Chuyển sang distributed mode (nếu chưa)
./switch_config.sh
# Chọn 'yes' để chuyển sang distributed

# Khởi động Frontend
cd frontend
npm run dev
```

**Mở trình duyệt:** `http://localhost:5173`

---

### Bước 3: MÁY 1 - Khởi động Simulator

```bash
cd may1_simulator

# Khởi động Simulator với IP máy 2
python3 parking_simulator.py --kafka-bootstrap 10.38.11.118:9092
```

---

## 🛑 DỪNG HỆ THỐNG

### Trên MÁY 2:
```bash
cd may2_kafka_spark
./stop_all_machine2.sh
```

### Trên MÁY 1:
- Nhấn `Ctrl+C` để dừng Simulator

### Trên MÁY 3:
- Nhấn `Ctrl+C` để dừng Frontend

---

## 🔍 KIỂM TRA KẾT NỐI

### Từ MÁY 1 hoặc MÁY 3, test kết nối đến MÁY 2:

```bash
# Test Kafka
telnet 10.38.11.118 9092
# Hoặc
nc -zv 10.38.11.118 9092

# Test WebSocket
telnet 10.38.11.118 5000
# Hoặc
curl http://10.38.11.118:5000
```

### Kiểm tra Kafka topics từ máy khác:

```bash
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-topics.sh \
  --list \
  --bootstrap-server 10.38.11.118:9092
```

### Kiểm tra messages trong topic:

```bash
# Input topic (từ Simulator)
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-console-consumer.sh \
  --bootstrap-server 10.38.11.118:9092 \
  --topic parking-raw-events \
  --from-beginning

# Output topic (từ Spark)
/home/phanvantai/Downloads/kafka_2.13-3.7.0/bin/kafka-console-consumer.sh \
  --bootstrap-server 10.38.11.118:9092 \
  --topic parking-processed-results \
  --from-beginning
```

---

## ⚠️ TROUBLESHOOTING

### 1. Kafka không kết nối được từ máy khác

**Nguyên nhân:**
- Firewall chặn port 9092
- `advertised.listeners` chưa đúng

**Giải pháp:**
```bash
# Trên MÁY 2, kiểm tra firewall
sudo ufw status
sudo ufw allow 9092/tcp  # Nếu cần

# Kiểm tra cấu hình Kafka
grep -E "listeners=|advertised.listeners=" \
  /home/phanvantai/Downloads/kafka_2.13-3.7.0/config/server.properties

# Nếu sai, chạy lại:
cd may2_kafka_spark
./update_kafka_config.sh
./stop_kafka.sh
./start_kafka.sh
```

### 2. WebSocket không kết nối được

**Kiểm tra:**
- Backend đã chạy chưa: `ps aux | grep kafka_websocket_server`
- Port 5000 có bị chiếm không: `netstat -tuln | grep 5000`
- Firewall: `sudo ufw allow 5000/tcp`

### 3. Frontend không hiển thị dữ liệu

**Kiểm tra:**
- WebSocket đã kết nối chưa (xem console trong browser)
- Config đã đúng chưa: `cat may3_visualization_react/config.json`
- Backend có nhận được dữ liệu từ Kafka không (xem log)

### 4. Spark Processor không xử lý dữ liệu

**Kiểm tra:**
- Spark đã chạy chưa: `ps aux | grep spark-submit`
- Kafka có dữ liệu không: kiểm tra topic `parking-raw-events`
- Log Spark: `tail -f may2_kafka_spark/logs/spark_processor_*.log`

---

## 📝 CẤU HÌNH CHI TIẾT

### Kafka (MÁY 2)
- **File config**: `/home/phanvantai/Downloads/kafka_2.13-3.7.0/config/server.properties`
- **Listeners**: `PLAINTEXT://0.0.0.0:9092`
- **Advertised Listeners**: `PLAINTEXT://10.38.11.118:9092`

### Spark Processor (MÁY 2)
- **Kafka Bootstrap**: `localhost:9092` (vì chạy trên cùng máy)
- **Input Topic**: `parking-raw-events`
- **Output Topic**: `parking-processed-results`

### WebSocket Backend (MÁY 2)
- **Kafka Bootstrap**: `10.38.11.118:9092` (từ `config.json`)
- **WebSocket Host**: `0.0.0.0`
- **WebSocket Port**: `5000`

### React Frontend (MÁY 3)
- **WebSocket URL**: `http://10.38.11.118:5000` (từ `config.json`)

---

## ✅ CHECKLIST KHỞI ĐỘNG

- [ ] MÁY 2: Kafka đã khởi động và listen trên port 9092
- [ ] MÁY 2: Topics đã được tạo (`parking-raw-events`, `parking-processed-results`)
- [ ] MÁY 2: Spark Processor đang chạy
- [ ] MÁY 2: WebSocket Backend đang chạy trên port 5000
- [ ] MÁY 3: Frontend đã chuyển sang distributed mode
- [ ] MÁY 3: Frontend đang chạy và kết nối được WebSocket
- [ ] MÁY 1: Simulator đang chạy với `--kafka-bootstrap 10.38.11.118:9092`
- [ ] Kiểm tra dữ liệu: Simulator → Kafka → Spark → Kafka → WebSocket → Frontend

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề, kiểm tra:
1. Logs của từng service
2. Kết nối mạng giữa các máy
3. Firewall settings
4. Cấu hình IP trong các file config

