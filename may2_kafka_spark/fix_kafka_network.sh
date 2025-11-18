#!/bin/bash
# Script để sửa cấu hình Kafka để có thể kết nối từ máy khác

KAFKA_HOME=${KAFKA_HOME:-/home/phanvantai/Downloads/kafka_2.13-3.7.0}
CONFIG_FILE="$KAFKA_HOME/config/server.properties"

echo "=========================================="
echo "Sửa cấu hình Kafka để cho phép kết nối từ xa"
echo "=========================================="

# Lấy IP của máy
MACHINE_IP=$(hostname -I | awk '{print $1}')
echo "IP của máy này: $MACHINE_IP"

# Backup config file
if [ ! -f "$CONFIG_FILE.backup" ]; then
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
    echo "✅ Đã backup config file"
fi

# Sửa listeners để listen trên tất cả interfaces
sed -i 's/^#listeners=PLAINTEXT:\/\/:9092/listeners=PLAINTEXT:\/\/0.0.0.0:9092/' "$CONFIG_FILE"
sed -i 's/^listeners=PLAINTEXT:\/\/localhost:9092/listeners=PLAINTEXT:\/\/0.0.0.0:9092/' "$CONFIG_FILE"
sed -i 's/^listeners=PLAINTEXT:\/\/:9092/listeners=PLAINTEXT:\/\/0.0.0.0:9092/' "$CONFIG_FILE"

# Sửa advertised.listeners để advertise đúng IP
if grep -q "^advertised.listeners" "$CONFIG_FILE"; then
    sed -i "s|^advertised.listeners=.*|advertised.listeners=PLAINTEXT://$MACHINE_IP:9092|" "$CONFIG_FILE"
else
    # Thêm dòng mới nếu chưa có
    echo "" >> "$CONFIG_FILE"
    echo "# Advertised listeners - cho phép kết nối từ máy khác" >> "$CONFIG_FILE"
    echo "advertised.listeners=PLAINTEXT://$MACHINE_IP:9092" >> "$CONFIG_FILE"
fi

# Đảm bảo listener.security.protocol.map được set
if ! grep -q "^listener.security.protocol.map" "$CONFIG_FILE"; then
    echo "" >> "$CONFIG_FILE"
    echo "listener.security.protocol.map=PLAINTEXT:PLAINTEXT" >> "$CONFIG_FILE"
fi

echo ""
echo "✅ Đã sửa cấu hình Kafka"
echo ""
echo "Các thay đổi:"
echo "  - listeners: PLAINTEXT://0.0.0.0:9092 (listen trên tất cả interfaces)"
echo "  - advertised.listeners: PLAINTEXT://$MACHINE_IP:9092"
echo ""
echo "⚠️  QUAN TRỌNG: Bạn cần khởi động lại Kafka để áp dụng thay đổi!"
echo ""
echo "Để khởi động lại:"
echo "  1. ./stop_kafka.sh"
echo "  2. ./start_kafka.sh"
echo ""

