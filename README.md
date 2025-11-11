# HỆ THỐNG BÃI ĐỖ XE REAL-TIME

Hệ thống tính toán tiền đỗ xe theo thời gian thực sử dụng Kafka và Spark Stateful Processing.

## Kiến trúc hệ thống

```
┌─────────────┐
│  MÁY 1      │
│  Simulator  │───[Kafka Producer]───┐
└─────────────┘                       │
                                      ▼
                              ┌───────────────┐
                              │  MÁY 2        │
                              │  Kafka Broker │
                              │  Topic:       │
                              │  parking-raw  │
                              └───────┬───────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │  MÁY 2        │
                              │  Spark        │
                              │  Stateful     │
                              │  Processing   │
                              └───────┬───────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │  MÁY 2        │
                              │  Kafka Broker │
                              │  Topic:       │
                              │  parking-     │
                              │  processed   │
                              └───────┬───────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │  MÁY 3        │
                              │  Visualization│
                              │  GUI          │
                              └───────────────┘
```

## Cấu trúc thư mục

```
hw02/
├── may1_simulator/          # Máy 1: Simulator
│   ├── parking_simulator.py
│   ├── requirements.txt
│   └── README.md
├── may2_kafka_spark/        # Máy 2: Kafka + Spark
│   ├── spark_processor.py
│   ├── create_topics.sh
│   ├── requirements.txt
│   └── README.md
├── may3_visualization/      # Máy 3: Visualization
│   ├── visualization.py
│   ├── requirements.txt
│   └── README.md
└── README.md                # File này
```

## Yêu cầu hệ thống

### Máy 1 (Simulator)
- Python 3.8+
- Kết nối mạng đến Máy 2

### Máy 2 (Kafka + Spark)
- Java 8 hoặc 11
- Apache Kafka 2.8+ hoặc 3.x
- Apache Spark 4.0.1
- Python 3.8+
- Tối thiểu 4GB RAM

### Máy 3 (Visualization)
- Python 3.8+
- Streamlit
- Kết nối mạng đến Máy 2

## Hướng dẫn setup và chạy

### Bước 1: Setup Máy 2 (Kafka + Spark)

1. Cài đặt Kafka và Spark theo hướng dẫn trong `may2_kafka_spark/README.md`
2. Khởi động Kafka broker
3. Tạo Kafka topics:
   ```bash
   cd may2_kafka_spark
   chmod +x create_topics.sh
   ./create_topics.sh
   ```

### Bước 2: Setup Máy 1 (Simulator)

1. Cài đặt dependencies:
   ```bash
   cd may1_simulator
   pip install -r requirements.txt
   ```

2. Chạy simulator:
   ```bash
   python parking_simulator.py --kafka-bootstrap <IP_MÁY_2>:9092
   ```

### Bước 3: Setup Máy 2 (Spark Processing)

1. Cài đặt dependencies:
   ```bash
   cd may2_kafka_spark
   pip install -r requirements.txt
   ```

2. Chạy Spark processing:
   ```bash
   spark-submit \
     --packages org.apache.spark:spark-sql-kafka-0-10_2.12:4.0.1 \
     spark_processor.py \
     --kafka-bootstrap localhost:9092
   ```

### Bước 4: Setup Máy 3 (Visualization)

1. Cài đặt dependencies:
   ```bash
   cd may3_visualization
   pip install -r requirements.txt
   ```

2. Chạy visualization:
   ```bash
   streamlit run visualization.py
   ```
   Sau đó mở trình duyệt và cấu hình Kafka trong sidebar

## Thứ tự khởi động

1. **Máy 2**: Khởi động Kafka broker và tạo topics
2. **Máy 2**: Khởi động Spark processing
3. **Máy 1**: Khởi động Simulator
4. **Máy 3**: Khởi động Visualization

## Tính năng chính

### Simulator (Máy 1)
- Sinh dữ liệu mô phỏng camera AI
- Gửi events về trạng thái xe (ENTERING, PARKED, MOVING, EXITING)
- Quản lý nhiều xe đồng thời

### Spark Processing (Máy 2)
- Xử lý stateful để tracking từng xe
- Tính toán tiền đỗ xe theo block 10 phút
- Cập nhật định kỳ thời gian đỗ và tiền
- Xử lý các trạng thái: ENTERING → PARKED → MOVING → EXITING

### Visualization (Máy 3)
- Hiển thị bản đồ bãi xe real-time
- Chi tiết từng xe đang đỗ
- Thống kê tổng quan
- Cập nhật tự động khi có dữ liệu mới

## Format dữ liệu

### Input (Simulator → Kafka)
```json
{
  "timestamp": "2024-01-01 10:30:45",
  "timestamp_unix": 1704094245,
  "license_plate": "29A-12345",
  "location": "A1",
  "status_code": "PARKED"
}
```

### Output (Spark → Visualization)
```json
{
  "timestamp": "2024-01-01 10:30:45",
  "timestamp_unix": 1704094245,
  "license_plate": "29A-12345",
  "location": "A1",
  "status": "PARKED",
  "action": "parking_updated",
  "parked_duration_minutes": 15.5,
  "parked_blocks": 2,
  "total_cost": 20000,
  "event_type": "vehicle_event"
}
```

## Tính tiền đỗ xe

- Tính theo block 10 phút
- Làm tròn lên (ví dụ: 5 phút = 1 block, 15 phút = 2 blocks)
- Giá mỗi block: 10,000 VNĐ (có thể thay đổi trong code)

## Troubleshooting

### Simulator không gửi được dữ liệu
- Kiểm tra kết nối đến Máy 2
- Kiểm tra Kafka broker đã chạy chưa
- Kiểm tra topic đã được tạo chưa

### Spark không xử lý được
- Kiểm tra Spark version phải là 4.0.1
- Kiểm tra Kafka connector đã được load chưa
- Xem logs trong Spark UI (http://localhost:4040)

### Visualization không hiển thị
- Kiểm tra có nhận được dữ liệu từ Kafka không
- Kiểm tra format dữ liệu có đúng không
- Xem log để biết chi tiết lỗi

## Tài liệu chi tiết

Xem README.md trong từng folder để biết chi tiết:
- `may1_simulator/README.md`
- `may2_kafka_spark/README.md`
- `may3_visualization/README.md`

## License

Dự án này được tạo cho mục đích học tập.

# hw01_bigdata
