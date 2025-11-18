# 📋 Hướng Dẫn Cấu Hình - Local vs Distributed Mode

## 🎯 Tổng Quan

Hệ thống hỗ trợ 2 chế độ chạy:

1. **LOCAL Mode** (1 máy): Chạy tất cả trên 1 máy, dùng `localhost`
2. **DISTRIBUTED Mode** (nhiều máy): Chạy phân tán trên nhiều máy, dùng IP thực tế

## 🔄 Chuyển Đổi Mode

### Cách 1: Dùng Script (Khuyên dùng)

```bash
cd may3_visualization_react
./switch_config.sh
```

Script sẽ:
- Hiển thị mode hiện tại
- Hỏi bạn muốn chuyển sang mode nào
- Tự động copy config và cập nhật frontend

### Cách 2: Thủ công

```bash
# Chuyển sang LOCAL mode
cp config.local.json config.json
cp config.json frontend/public/config.json

# Chuyển sang DISTRIBUTED mode
cp config.distributed.json config.json
cp config.json frontend/public/config.json
```

## 📁 Cấu Trúc File Config

```
may3_visualization_react/
├── config.json              # Config hiện tại (được sử dụng)
├── config.local.json        # Template cho LOCAL mode
├── config.distributed.json  # Template cho DISTRIBUTED mode
└── frontend/public/
    └── config.json          # Copy của config.json (cho frontend)
```

## 🔧 Cấu Hình Chi Tiết

### LOCAL Mode (config.local.json)

```json
{
  "mode": "local",
  "backend": {
    "kafka": {
      "bootstrap_servers": "localhost:9092",
      "topic": "parking-processed-results"
    },
    "websocket": {
      "host": "0.0.0.0",
      "port": 5000
    }
  },
  "frontend": {
    "websocket_url": "http://localhost:5000"
  }
}
```

**Sử dụng khi:**
- ✅ Chạy tất cả trên 1 máy
- ✅ Không ở trường
- ✅ Test local

### DISTRIBUTED Mode (config.distributed.json)

```json
{
  "mode": "distributed",
  "backend": {
    "kafka": {
      "bootstrap_servers": "10.38.11.118:9092",
      "topic": "parking-processed-results"
    },
    "websocket": {
      "host": "0.0.0.0",
      "port": 5000
    }
  },
  "frontend": {
    "websocket_url": "http://10.38.11.118:5000"
  }
}
```

**Sử dụng khi:**
- ✅ Ở trường
- ✅ Chạy trên nhiều máy
- ✅ Máy 2 (Kafka + Spark) có IP: `10.38.11.118`

**Lưu ý:** Cần cập nhật IP trong `config.distributed.json` nếu IP máy 2 khác.

## 🚀 Cách Sử Dụng

### Khi Ở Nhà (LOCAL Mode)

1. **Chuyển sang LOCAL mode:**
   ```bash
   cd may3_visualization_react
   ./switch_config.sh
   # Chọn 1 hoặc nhập 'yes' để chuyển sang local
   ```

2. **Chạy backend:**
   ```bash
   cd backend
   source venv/bin/activate
   python3 kafka_websocket_server.py
   ```

3. **Chạy frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

4. **Mở browser:** `http://localhost:5173`

### Khi Ở Trường (DISTRIBUTED Mode)

1. **Cập nhật IP trong config.distributed.json:**
   ```bash
   # Sửa IP máy 2 nếu khác 10.38.11.118
   nano config.distributed.json
   ```

2. **Chuyển sang DISTRIBUTED mode:**
   ```bash
   cd may3_visualization_react
   ./switch_config.sh
   # Chọn 2 hoặc nhập 'yes' để chuyển sang distributed
   ```

3. **Trên Máy 2 (Kafka + Spark + Backend):**
   ```bash
   # Khởi động Kafka
   cd may2_kafka_spark
   ./start_kafka.sh
   
   # Khởi động Spark Processor
   ./run_spark_server.sh
   
   # Khởi động WebSocket Backend
   cd ../may3_visualization_react/backend
   source venv/bin/activate
   python3 kafka_websocket_server.py
   ```

4. **Trên Máy 3 (Frontend):**
   ```bash
   cd may3_visualization_react/frontend
   npm run dev
   ```

5. **Mở browser:** `http://localhost:5173` (trên máy 3)

## 🔍 Kiểm Tra Cấu Hình

### Xem config hiện tại:
```bash
cat may3_visualization_react/config.json | grep -A 5 '"mode"'
```

### Xem config frontend:
```bash
cat may3_visualization_react/frontend/public/config.json | grep -A 5 '"mode"'
```

### Kiểm tra backend đã load config đúng chưa:
Khi khởi động backend, xem log:
```
✅ Đã load config từ /path/to/config.json
   Mode: local (hoặc distributed)
📋 Cấu hình Kafka: localhost:9092 (hoặc 10.38.11.118:9092)
📋 WebSocket: 0.0.0.0:5000
```

### Kiểm tra frontend đã load config đúng chưa:
Mở browser console (F12), xem log:
```
✅ Đã load config: mode=local, WebSocket URL=http://localhost:5000
```

## ⚠️ Lưu Ý Quan Trọng

1. **Sau khi chuyển config, cần khởi động lại:**
   - Backend: Dừng và chạy lại `kafka_websocket_server.py`
   - Frontend: Dừng và chạy lại `npm run dev` (hoặc refresh browser)

2. **Kafka cấu hình:**
   - LOCAL mode: Kafka phải chạy trên `localhost:9092`
   - DISTRIBUTED mode: Kafka phải được cấu hình `advertised.listeners` đúng IP

3. **Firewall:**
   - DISTRIBUTED mode: Đảm bảo port 5000 và 9092 không bị firewall chặn

4. **IP Address:**
   - Cập nhật IP trong `config.distributed.json` nếu IP máy 2 thay đổi

## 🐛 Troubleshooting

### Backend không kết nối được Kafka
- Kiểm tra config: `cat config.json | grep bootstrap_servers`
- Kiểm tra Kafka đang chạy: `netstat -tuln | grep 9092`
- Kiểm tra IP/port đúng chưa

### Frontend không kết nối được WebSocket
- Kiểm tra config frontend: `cat frontend/public/config.json`
- Kiểm tra backend đang chạy: `netstat -tuln | grep 5000`
- Xem console browser (F12) để xem lỗi

### Config không được load
- Đảm bảo `config.json` tồn tại trong thư mục gốc
- Đảm bảo `frontend/public/config.json` tồn tại
- Kiểm tra format JSON đúng (dùng `jq` hoặc online validator)

