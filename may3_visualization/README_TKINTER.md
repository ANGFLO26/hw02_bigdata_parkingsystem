# MÁY 3: VISUALIZATION (Tkinter Dashboard)

## Mô tả
Ứng dụng visualization bãi đỗ xe sử dụng Tkinter để hiển thị dashboard real-time.

## Chức năng
- ✅ Đọc dữ liệu từ Kafka topic `parking-processed-results`
- ✅ Hiển thị bản đồ bãi xe với các vị trí occupied/available
- ✅ Hiển thị chi tiết từng xe đang đỗ (biển số, thời gian đỗ, tiền phải trả)
- ✅ Cập nhật real-time khi có dữ liệu mới
- ✅ Thống kê tổng quan: số chỗ đã đỗ, trống, tổng doanh thu
- ✅ Log window để theo dõi các events

## Yêu cầu hệ thống
- Python 3.8 trở lên
- Tkinter (thường có sẵn với Python)
- Kết nối mạng đến Máy 2 (Kafka Broker)

## Cài đặt

### 1. Cài đặt Python dependencies
```bash
cd may3_visualization
pip install -r requirements.txt
```

**Lưu ý:** Tkinter thường có sẵn với Python. Nếu không có, cài đặt:
- Ubuntu/Debian: `sudo apt-get install python3-tk`
- CentOS/RHEL: `sudo yum install python3-tkinter`
- macOS: Tkinter có sẵn với Python từ python.org

## Chạy chương trình

### Chạy ứng dụng Tkinter
```bash
cd may3_visualization
python3 visualization_tkinter.py
```

Hoặc:
```bash
./visualization_tkinter.py
```

## Cấu hình

### Trong giao diện:
1. **Kafka Bootstrap Servers**: Nhập địa chỉ Kafka broker
   - Mặc định: `10.38.11.118:9092`
   - Format: `<IP_MÁY_2>:9092`

2. **Kafka Topic**: Tên topic để đọc dữ liệu
   - Mặc định: `parking-processed-results`

3. Nhấn nút **"🔄 Kết nối/Khởi động lại"** để bắt đầu

4. Nhấn nút **"⏹️ Dừng"** để dừng kết nối

## Giao diện

### Phần trên: Thống kê
- **Tổng số chỗ**: 60 chỗ
- **Đã đỗ**: Số chỗ đang có xe (màu đỏ)
- **Trống**: Số chỗ còn trống (màu xanh)
- **Doanh thu**: Tổng doanh thu hiện tại (màu xanh dương)

### Phần giữa trái: Bản đồ bãi xe
- Hiển thị 6 tầng (A, B, C, D, E, F)
- Mỗi tầng có 10 chỗ (1-10)
- **Màu xanh lá**: Vị trí trống
- **Màu đỏ**: Vị trí có xe đỗ
  - Hiển thị: Vị trí, biển số, thời gian đỗ, tiền phải trả

### Phần giữa phải: Bảng chi tiết
- Hiển thị danh sách tất cả xe đang đỗ
- Cột: Vị trí, Biển số, Thời gian đỗ (phút), Số block, Tiền (VNĐ)
- Tự động cập nhật khi có dữ liệu mới

### Phần dưới: Log
- Hiển thị các events và log messages
- Giúp debug và theo dõi hoạt động

## Xử lý dữ liệu

Ứng dụng tự động xử lý các loại events:

1. **vehicle_entered**: Xe mới vào
   - Thêm vào bản đồ với status ENTERING
   - Thời gian đỗ = 0, Tiền = 0

2. **vehicle_parked / parking_updated / periodic_update**: Xe đã đỗ hoặc cập nhật
   - Cập nhật thông tin: thời gian đỗ, số block, tiền phải trả
   - Status = PARKED

3. **vehicle_exiting**: Xe đang ra
   - Xóa khỏi bản đồ và bảng chi tiết

## Format dữ liệu từ Kafka

Ứng dụng xử lý dữ liệu với format:
```json
{
    "timestamp": "2025-11-12T11:33:33.000+07:00",
    "timestamp_unix": 1762922013,
    "license_plate": "('30B-55555',)",  // Tự động parse thành "30B-55555"
    "location": "E3",
    "status": "PARKED",
    "action": "parking_updated",
    "parked_duration_minutes": 4.733333333333333,
    "parked_blocks": 1,
    "total_cost": 10000,
    "event_type": "vehicle_event"
}
```

**Lưu ý:** `license_plate` có thể có format tuple string `('30B-55555',)` - ứng dụng tự động parse thành `30B-55555`.

## Troubleshooting

### Không kết nối được đến Kafka:
1. Kiểm tra IP Máy 2 có đúng không
2. Kiểm tra Kafka đã chạy trên Máy 2 chưa
3. Kiểm tra firewall có chặn port 9092 không
4. Xem log window để biết lỗi cụ thể

### Không hiển thị dữ liệu:
1. Kiểm tra topic name có đúng không (`parking-processed-results`)
2. Kiểm tra Máy 1 có đang gửi dữ liệu không
3. Kiểm tra Máy 2 (Spark) có đang xử lý và ghi dữ liệu không
4. Xem log window để debug

### Ứng dụng chạy chậm:
- Giảm tần suất update (sửa `self.root.after(2000, ...)` thành giá trị lớn hơn)
- Kiểm tra kết nối mạng đến Máy 2

## So sánh với Streamlit

### Ưu điểm của Tkinter:
- ✅ Không cần server, chạy trực tiếp như desktop app
- ✅ Nhẹ hơn, không cần trình duyệt
- ✅ Tốc độ nhanh hơn
- ✅ Dễ deploy, chỉ cần Python

### Nhược điểm:
- ❌ Giao diện đơn giản hơn Streamlit
- ❌ Không có responsive design
- ❌ Không có nhiều widgets như Streamlit

## Tùy chỉnh

### Thay đổi màu sắc:
Sửa trong hàm `create_parking_map()`:
- Occupied: `#ff6b6b` (đỏ)
- Available: `#51cf66` (xanh lá)

### Thay đổi tần suất update:
Sửa trong hàm `update_display()`:
```python
self.root.after(2000, self.update_display)  # 2000ms = 2 giây
```

### Thay đổi số lượng chỗ:
Sửa biến `ALL_LOCATIONS` và `total_locations` trong `__init__()`.

