#!/bin/bash
# Script để cập nhật cấu hình Kafka với IP chính xác

KAFKA_HOME=${KAFKA_HOME:-/home/phanvantai/Downloads/kafka_2.13-3.7.0}
CONFIG_FILE="$KAFKA_HOME/config/server.properties"

# IP của máy (Máy 2)
MACHINE_IP="10.38.11.118"

echo "=========================================="
echo "Cập nhật cấu hình Kafka"
echo "=========================================="
echo "IP Máy 2: $MACHINE_IP"
echo ""

# Backup nếu chưa có
if [ ! -f "$CONFIG_FILE.backup" ]; then
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
    echo "✅ Đã backup config file"
fi

# Cập nhật listeners để listen trên tất cả interfaces
sed -i 's|^listeners=.*|listeners=PLAINTEXT://0.0.0.0:9092|' "$CONFIG_FILE"

# Cập nhật advertised.listeners với IP chính xác
if grep -q "^advertised.listeners" "$CONFIG_FILE"; then
    sed -i "s|^advertised.listeners=.*|advertised.listeners=PLAINTEXT://$MACHINE_IP:9092|" "$CONFIG_FILE"
else
    # Thêm nếu chưa có
    echo "" >> "$CONFIG_FILE"
    echo "# Advertised listeners - cho phép kết nối từ máy khác" >> "$CONFIG_FILE"
    echo "advertised.listeners=PLAINTEXT://$MACHINE_IP:9092" >> "$CONFIG_FILE"
fi

# Đảm bảo listener.security.protocol.map
if ! grep -q "^listener.security.protocol.map" "$CONFIG_FILE"; then
    echo "listener.security.protocol.map=PLAINTEXT:PLAINTEXT" >> "$CONFIG_FILE"
fi

echo ""
echo "✅ Đã cập nhật cấu hình:"
echo "   listeners=PLAINTEXT://0.0.0.0:9092"
echo "   advertised.listeners=PLAINTEXT://$MACHINE_IP:9092"
echo ""
echo "📋 Kiểm tra cấu hình:"
grep -E "^listeners=|^advertised.listeners=" "$CONFIG_FILE"
echo ""
