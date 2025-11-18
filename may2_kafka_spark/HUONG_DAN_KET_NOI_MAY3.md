# HƯỚNG DẪN KẾT NỐI MÁY 3 ĐẾN MÁY 2

## 🔍 Vấn đề

Máy 3 không thể kết nối đến Kafka trên Máy 2 vì cấu hình `advertised.listeners` chưa đúng.

## ✅ Giải pháp

### Bước 1: Cập nhật cấu hình Kafka trên Máy 2

**File cấu hình:** `/home/phanvantai/Downloads/kafka_2.13-3.7.0/config/server.properties`

**Cần sửa 2 dòng:**

```properties
# Listen trên tất cả interfaces để nhận kết nối từ xa
listeners=PLAINTEXT://0.0.0.0:9092

# Advertise IP của Máy 2 để Máy 3 biết kết nối đến đâu
advertised.listeners=PLAINTEXT://10.38.11.118:9092
```

**Lưu ý:** Thay `10.38.11.118` bằng IP thực tế của Máy 2 nếu khác.

### Bước 2: Khởi động lại Kafka trên Máy 2

```bash
cd may2_kafka_spark

# Dừng Kafka
./stop_kafka.sh

# Khởi động lại Kafka với cấu hình mới
./start_kafka.sh
```

### Bước 3: Kiểm tra Kafka đã listen đúng chưa

```bash
# Kiểm tra port 9092 đang listen trên tất cả interfaces
netstat -tuln | grep 9092
# Hoặc
ss -tuln | grep 9092

# Kết quả mong đợi:
# tcp6  0  0 :::9092  :::*  LISTEN
# (hoặc tcp  0  0 0.0.0.0:9092  0.0.0.0:*  LISTEN)
```

### Bước 4: Cấu hình trên Máy 3

1. **Chạy Streamlit:**
   ```bash
   cd may3_visualization
   streamlit run visualization.py
   ```

2. **Trong giao diện Streamlit:**
   - **Kafka Bootstrap Servers:** Nhập `10.38.11.118:9092` (IP của Máy 2)
   - **Kafka Topic:** Nhập `parking-processed-results`
   - Nhấn nút **"🔄 Kết nối/Khởi động lại"**

## 🔧 Script tự động cập nhật cấu hình

Đã có script `update_kafka_config.sh` để tự động cập nhật:

```bash
cd may2_kafka_spark
./update_kafka_config.sh
```

Sau đó khởi động lại Kafka:
```bash
./stop_kafka.sh
./start_kafka.sh
```

## ✅ Kiểm tra kết nối

### Từ Máy 3, test kết nối đến Máy 2:

```bash
# Test kết nối TCP đến port 9092
telnet 10.38.11.118 9092
# Hoặc
nc -zv 10.38.11.118 9092
```

Nếu kết nối thành công, bạn sẽ thấy:
```
Connection to 10.38.11.118 9092 port [tcp/*] succeeded!
```

## 🐛 Troubleshooting

### Nếu vẫn không kết nối được:

1. **Kiểm tra firewall:**
   ```bash
   # Trên Máy 2
   sudo ufw status
   # Nếu firewall đang chạy, mở port 9092:
   sudo ufw allow 9092/tcp
   ```

2. **Kiểm tra Kafka log:**
   ```bash
   tail -f /home/phanvantai/Downloads/kafka_2.13-3.7.0/logs/kafka.log
   ```

3. **Kiểm tra IP của Máy 2:**
   ```bash
   hostname -I
   # Đảm bảo IP này khớp với advertised.listeners
   ```

4. **Kiểm tra từ Máy 3:**
   ```bash
   # Test ping
   ping 10.38.11.118
   
   # Test port
   telnet 10.38.11.118 9092
   ```

## 📝 Tóm tắt

**Quan trọng nhất:**
- `listeners=PLAINTEXT://0.0.0.0:9092` - để Kafka listen trên tất cả interfaces
- `advertised.listeners=PLAINTEXT://10.38.11.118:9092` - để Máy 3 biết kết nối đến đâu
- **Phải khởi động lại Kafka** sau khi sửa config!

