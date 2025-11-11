# MÁY 1: SIMULATOR (Data Generator)

## Mô tả
Máy này đóng vai trò sinh dữ liệu mô phỏng camera AI về trạng thái các vị trí đỗ xe và gửi lên Kafka topic.

## Chức năng
- Sinh dữ liệu events về trạng thái xe (ENTERING, PARKED, MOVING, EXITING)
- Gửi dữ liệu lên Kafka topic `parking-raw-events`
- Quản lý trạng thái của nhiều xe đồng thời
- Theo dõi vị trí đỗ và biển số xe

## Yêu cầu hệ thống
- Python 3.8 trở lên
- Kết nối mạng đến Máy 2 (Kafka Broker)

## Cài đặt

### 1. Cài đặt Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Cấu hình
Chỉnh sửa các tham số trong lệnh chạy hoặc dùng arguments:
- `--kafka-bootstrap`: Địa chỉ Kafka broker (ví dụ: `192.168.1.100:9092`)
- `--topic`: Tên Kafka topic (mặc định: `parking-raw-events`)
- `--duration`: Thời gian chạy simulator (phút, mặc định: 30)
- `--interval`: Thời gian trung bình giữa các events (giây, mặc định: 3.0)

## Chạy chương trình

### Chạy với cấu hình mặc định
```bash
python parking_simulator.py
```

### Chạy với các tham số tùy chỉnh
```bash
python parking_simulator.py \
    --kafka-bootstrap 192.168.1.100:9092 \
    --topic parking-raw-events \
    --duration 60 \
    --interval 2.0
```

### Ví dụ kết nối đến Máy 2
```bash
python parking_simulator.py --kafka-bootstrap <IP_MÁY_2>:9092
```

## Format dữ liệu output

Mỗi event được gửi lên Kafka có format JSON:
```json
{
  "timestamp": "2024-01-01 10:30:45",
  "timestamp_unix": 1704094245,
  "license_plate": "29A-12345",
  "location": "A1",
  "status_code": "PARKED"
}
```

### Các trạng thái (status_code)
- `ENTERING`: Xe đang vào bãi
- `PARKED`: Xe đã đỗ
- `MOVING`: Xe đang di chuyển
- `EXITING`: Xe đang ra khỏi bãi

## Cấu trúc dữ liệu

### Biển số xe
- 50 biển số mẫu (29A-xxxxx, 30B-xxxxx, ...)

### Vị trí đỗ
- 60 vị trí: A1-A10, B1-B10, C1-C10, D1-D10, E1-E10, F1-F10

## Monitoring

Chương trình sẽ in log định kỳ:
- Số lượng events đã gửi
- Số lượng gửi thành công/thất bại
- Số xe đang hoạt động
- Thời gian đã chạy

## Troubleshooting

### Lỗi kết nối Kafka
- Kiểm tra địa chỉ Kafka broker có đúng không
- Kiểm tra kết nối mạng đến Máy 2
- Kiểm tra Kafka broker đã chạy chưa

### Lỗi gửi dữ liệu
- Kiểm tra topic `parking-raw-events` đã được tạo chưa
- Kiểm tra quyền gửi dữ liệu lên topic
- Xem log để biết chi tiết lỗi

## Dừng chương trình
Nhấn `Ctrl+C` để dừng simulator. Chương trình sẽ in thống kê cuối cùng trước khi thoát.

