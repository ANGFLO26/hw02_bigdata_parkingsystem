# 🚗 Bãi Đỗ Xe - React Visualization

Ứng dụng visualization real-time cho hệ thống bãi đỗ xe sử dụng React và WebSocket.

## 📋 Tính năng

- ✅ Hiển thị bản đồ bãi đỗ theo tầng (A-F), mỗi tầng 10 chỗ
- ✅ Màu xanh = chỗ trống, màu đỏ = chỗ đã đỗ
- ✅ Tính tiền real-time khi xe đang đỗ
- ✅ Tính tiền khi xe ra
- ✅ Thống kê: tổng chỗ, đã đỗ, trống, doanh thu
- ✅ Bảng chi tiết xe đang đỗ
- ✅ WebSocket real-time updates

## 🏗️ Cấu trúc

```
may3_visualization_react/
├── backend/                    # Python Flask + WebSocket server
│   ├── kafka_websocket_server.py
│   └── requirements.txt
└── frontend/                   # React app
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   │   ├── Statistics.jsx
    │   │   ├── ParkingMap.jsx
    │   │   └── VehicleTable.jsx
    │   └── ...
    └── package.json
```

## 🚀 Cài đặt và Chạy

### Backend (Máy 2)

1. **Cài đặt dependencies:**
```bash
cd may3_visualization_react/backend
pip install -r requirements.txt
```

2. **Chạy WebSocket server:**
```bash
python3 kafka_websocket_server.py
```

Server sẽ chạy trên `http://localhost:5000`

### Frontend

1. **Cài đặt dependencies:**
```bash
cd may3_visualization_react/frontend
npm install
```

2. **Chạy development server:**
```bash
npm run dev
```

Ứng dụng sẽ mở tại `http://localhost:5173`

## 🔧 Cấu hình

### Backend

Mặc định kết nối đến:
- Kafka: `localhost:9092`
- Topic: `parking-processed-results`

Có thể sửa trong `kafka_websocket_server.py`:
```python
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "parking-processed-results"
```

### Frontend

Mặc định kết nối đến WebSocket server tại `http://localhost:5000`

Có thể sửa trong `src/App.jsx`:
```javascript
const SOCKET_URL = 'http://localhost:5000'
```

## 📊 Logic Tính Tiền

- **BLOCK_PRICE**: 10,000 VNĐ mỗi block 10 phút
- **Tính blocks**: `ceil(duration_minutes / 10)`
- **Tổng tiền**: `blocks * BLOCK_PRICE`
- **Real-time**: Tính lại mỗi 2 giây khi xe đang đỗ
- **Khi xe ra**: Tính tiền cuối cùng dựa trên thời gian đỗ

## 🎨 Giao diện

- **Màu xanh**: Chỗ trống (available)
- **Màu đỏ**: Chỗ đã đỗ (occupied)
- **Gradient background**: Đẹp mắt, hiện đại
- **Responsive**: Tự động điều chỉnh theo kích thước màn hình

## 🧪 Test trên Máy 2

Để test trên máy 2 (không cần máy 1 và 3):

1. **Chạy Kafka và Spark Processor** (nếu chưa chạy):
```bash
cd may2_kafka_spark
./start_kafka.sh
./run_spark_server.sh
```

2. **Chạy backend WebSocket server:**
```bash
cd may3_visualization_react/backend
python3 kafka_websocket_server.py
```

3. **Chạy frontend React:**
```bash
cd may3_visualization_react/frontend
npm run dev
```

4. **Mở browser:** `http://localhost:5173`

5. **Gửi dữ liệu test** (nếu cần):
```bash
# Sử dụng may1_simulator hoặc gửi message trực tiếp vào Kafka
```

## 📝 Notes

- Backend tự động kết nối đến Kafka và stream data real-time
- Frontend nhận updates qua WebSocket mỗi 2 giây
- Tính tiền được cập nhật real-time khi xe đang đỗ
- Khi xe ra, hiển thị thông tin tiền cuối cùng

