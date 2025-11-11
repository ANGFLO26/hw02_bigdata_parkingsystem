# MÁY 3: VISUALIZATION (Streamlit Dashboard)

## Mô tả
Máy này đóng vai trò hiển thị giao diện dashboard real-time bằng Streamlit để theo dõi trạng thái bãi đỗ xe.

## Chức năng
- Đọc dữ liệu từ Kafka topic `parking-processed-results`
- Hiển thị bản đồ bãi xe với các vị trí occupied/available
- Hiển thị chi tiết từng xe đang đỗ (biển số, thời gian đỗ, tiền phải trả)
- Cập nhật real-time khi có dữ liệu mới
- Thống kê tổng quan: số chỗ đã đỗ, trống, tổng doanh thu

## Yêu cầu hệ thống
- Python 3.8 trở lên
- Streamlit
- Kết nối mạng đến Máy 2 (Kafka Broker)

## Cài đặt

### 1. Cài đặt Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Kiểm tra Streamlit
Sau khi cài đặt, kiểm tra:
```bash
streamlit --version
```

## Chạy chương trình

### Chạy Streamlit app
```bash
streamlit run visualization.py
```

Hoặc:
```bash
python -m streamlit run visualization.py
```

### Cấu hình trong giao diện
- Mở trình duyệt tại `http://localhost:8501`
- Sử dụng sidebar để cấu hình:
  - **Kafka Bootstrap Servers**: Địa chỉ Kafka broker (ví dụ: `localhost:9092` hoặc `192.168.1.100:9092`)
  - **Kafka Topic**: Tên topic (mặc định: `parking-processed-results`)
- Nhấn nút **"🔄 Kết nối/Khởi động lại"** để bắt đầu

### Ví dụ kết nối đến Máy 2
1. Chạy Streamlit: `streamlit run visualization.py`
2. Trong sidebar, nhập địa chỉ Kafka: `<IP_MÁY_2>:9092`
3. Nhấn "Kết nối/Khởi động lại"

## Giao diện

### Dashboard chính
- **Thống kê tổng quan**: 4 metrics cards hiển thị:
  - Tổng số chỗ
  - Đã đỗ (với delta số chỗ trống)
  - Trống
  - Doanh thu hiện tại

### Bản đồ bãi xe
- Hiển thị theo từng tầng (A, B, C, D, E, F)
- **Màu xanh lá**: Vị trí trống
- **Màu đỏ**: Vị trí có xe đỗ
- Mỗi ô hiển thị:
  - Vị trí (ví dụ: A1)
  - Biển số xe (nếu có)
  - Thời gian đỗ (phút)
  - Tiền phải trả (VNĐ)

### Bảng chi tiết
Hiển thị tất cả xe đang đỗ với thông tin:
- **Vị trí**: Location (A1, B3, ...)
- **Biển số**: License plate
- **Thời gian đỗ (phút)**: Số phút đã đỗ
- **Số block**: Số block 10 phút
- **Tiền (VNĐ)**: Số tiền phải trả

### Sidebar
- **Cấu hình**: Nhập địa chỉ Kafka và topic
- **Nút Kết nối**: Khởi động/khởi động lại kết nối Kafka
- **Nút Dừng**: Dừng consumer và ngừng cập nhật
- **Trạng thái**: Hiển thị trạng thái kết nối Kafka

## Format dữ liệu input

Chương trình đọc dữ liệu từ Kafka với format JSON:
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

### Các actions được xử lý
- `vehicle_entered`: Xe mới vào → Đánh dấu vị trí occupied
- `vehicle_parked`: Xe đã đỗ → Cập nhật thông tin
- `parking_updated`: Cập nhật thời gian đỗ và tiền
- `periodic_update`: Cập nhật định kỳ từ timer
- `vehicle_exiting`: Xe đang ra → Xóa khỏi bản đồ

## Tính năng

### Real-time update
- Tự động cập nhật khi nhận message mới từ Kafka
- Auto-refresh mỗi 2 giây để đảm bảo hiển thị mới nhất
- Sử dụng Streamlit session_state để lưu trữ dữ liệu

### Thread-safe
- Kafka consumer chạy trong thread riêng
- Session state được cập nhật an toàn từ consumer thread

### Connection management
- Hiển thị trạng thái kết nối Kafka trong sidebar
- Tự động reconnect nếu mất kết nối
- Có thể khởi động lại kết nối từ giao diện

## Troubleshooting

### Lỗi kết nối Kafka
- Kiểm tra địa chỉ Kafka broker có đúng không (trong sidebar)
- Kiểm tra kết nối mạng đến Máy 2
- Kiểm tra Kafka broker đã chạy chưa
- Kiểm tra topic `parking-processed-results` đã được tạo chưa
- Nhấn "Kết nối/Khởi động lại" để thử lại

### Streamlit không chạy
- Kiểm tra Streamlit đã cài đặt: `pip install streamlit`
- Kiểm tra Python version (phải >= 3.8)
- Xem log trong terminal để biết chi tiết lỗi

### Không nhận được dữ liệu
- Kiểm tra Spark processing đã chạy và gửi dữ liệu chưa
- Kiểm tra consumer group có đúng không
- Xem messages trong topic bằng kafka-console-consumer
- Kiểm tra trạng thái kết nối trong sidebar

### Hiển thị không cập nhật
- Kiểm tra có nhận được messages từ Kafka không (xem log terminal)
- Kiểm tra format dữ liệu có đúng không
- Thử nhấn "Kết nối/Khởi động lại" trong sidebar
- Kiểm tra trạng thái kết nối

### Port đã được sử dụng
Nếu port 8501 đã được sử dụng:
```bash
streamlit run visualization.py --server.port 8502
```

## Dừng chương trình
- Nhấn `Ctrl+C` trong terminal
- Hoặc nhấn nút "Dừng" trong sidebar và đóng trình duyệt

## Mở rộng

### Thêm tính năng
- Export dữ liệu ra file CSV/Excel (dùng `st.download_button`)
- Lưu lịch sử đỗ xe (dùng database hoặc file)
- Thống kê theo thời gian (dùng `st.line_chart`, `st.bar_chart`)
- Cảnh báo khi bãi đầy (dùng `st.warning` hoặc `st.error`)
- Biểu đồ doanh thu theo thời gian

### Tùy chỉnh giao diện
- Sửa file `visualization.py`
- Thay đổi màu sắc trong HTML/CSS
- Thêm các widgets Streamlit khác (selectbox, slider, etc.)
- Sử dụng `st.columns` để thay đổi layout

## Lưu ý

- Streamlit tự động refresh mỗi khi có thay đổi code (hot reload)
- Session state được giữ nguyên khi refresh trang
- Kafka consumer thread sẽ tự động dừng khi đóng ứng dụng
- Để chạy trên máy khác, truy cập `<IP_MÁY_3>:8501` (cần cấu hình firewall)
