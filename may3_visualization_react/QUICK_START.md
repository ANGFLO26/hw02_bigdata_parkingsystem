# 🚀 Quick Start

## 🎯 Chọn Mode

Hệ thống hỗ trợ 2 mode:
- **LOCAL Mode**: Chạy tất cả trên 1 máy (khi không ở trường)
- **DISTRIBUTED Mode**: Chạy phân tán trên nhiều máy (khi ở trường)

### Chuyển đổi mode:
```bash
cd may3_visualization_react
./switch_config.sh
```

Xem chi tiết: [CONFIG_GUIDE.md](./CONFIG_GUIDE.md)

---

## 🏠 LOCAL Mode - Chạy trên 1 Máy

### Bước 1: Cài đặt Dependencies

### Backend
```bash
cd may3_visualization_react/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend
```bash
cd may3_visualization_react/frontend
npm install
```

## Bước 2: Chạy Backend (Terminal 1)

```bash
cd may3_visualization_react/backend
source venv/bin/activate
python3 kafka_websocket_server.py
```

Bạn sẽ thấy:
```
🚀 Khởi động WebSocket server trên http://localhost:5000
✅ Đã kết nối đến Kafka: localhost:9092, Topic: parking-processed-results
```

## Bước 3: Chạy Frontend (Terminal 2)

```bash
cd may3_visualization_react/frontend
npm run dev
```

Bạn sẽ thấy:
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## Bước 4: Mở Browser

Mở trình duyệt và truy cập: **http://localhost:5173**

## Bước 5: Kiểm tra

1. ✅ Kiểm tra connection status: Phải hiển thị "🟢 Đã kết nối"
2. ✅ Kiểm tra mode indicator: Phải hiển thị "🏠 Local"
3. ✅ Kiểm tra bản đồ: Hiển thị 6 tầng (A-F), mỗi tầng 10 chỗ
4. ✅ Khi có xe vào: Chỗ đỗ chuyển từ xanh → đỏ
5. ✅ Khi xe đỗ: Tiền tăng dần theo thời gian real-time
6. ✅ Khi xe ra: Chỗ đỗ chuyển từ đỏ → xanh

---

## 🌐 DISTRIBUTED Mode - Chạy trên Nhiều Máy (Khi ở Trường)

### Bước 1: Chuyển sang DISTRIBUTED mode

```bash
cd may3_visualization_react
./switch_config.sh
# Chọn 2 hoặc nhập 'yes' để chuyển sang distributed
```

**Lưu ý:** Cập nhật IP trong `config.distributed.json` nếu IP máy 2 khác `10.38.11.118`

### Bước 2: Trên Máy 2 (Kafka + Spark + Backend)

```bash
# 1. Khởi động Kafka
cd may2_kafka_spark
./start_kafka.sh

# 2. Khởi động Spark Processor
./run_spark_server.sh

# 3. Khởi động WebSocket Backend
cd ../may3_visualization_react/backend
source venv/bin/activate
python3 kafka_websocket_server.py
```

### Bước 3: Trên Máy 3 (Frontend)

```bash
cd may3_visualization_react/frontend
npm install  # Nếu chưa cài
npm run dev
```

### Bước 4: Mở Browser

Trên máy 3, mở: **http://localhost:5173**

Kiểm tra:
- ✅ Mode indicator: Phải hiển thị "🌐 Distributed"
- ✅ Connection status: "🟢 Đã kết nối"

## Lưu ý

- **Kafka phải đang chạy** trên `localhost:9092`
- **Spark Processor** phải đang chạy để xử lý data
- **Topic** `parking-processed-results` phải có dữ liệu

## Troubleshooting

### Backend không kết nối được Kafka
```bash
# Kiểm tra Kafka
cd may2_kafka_spark
./start_kafka.sh

# Kiểm tra topic
python3 check_topic.py --kafka-bootstrap localhost:9092 --topic parking-processed-results
```

### Frontend không kết nối được WebSocket
- Kiểm tra backend đang chạy trên port 5000
- Kiểm tra firewall/network
- Xem console trong browser (F12) để xem lỗi

### Không có dữ liệu hiển thị
- Kiểm tra máy 1 (simulator) có đang gửi data không
- Kiểm tra Spark Processor có đang xử lý không
- Kiểm tra topic `parking-processed-results` có messages không

