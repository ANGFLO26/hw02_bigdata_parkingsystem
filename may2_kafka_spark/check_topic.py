#!/usr/bin/env python3
"""
Script để kiểm tra dữ liệu trên Kafka topic parking-processed-results
"""
from kafka import KafkaConsumer
import json
import sys

def check_topic(topic_name, max_messages=5):
    """Kiểm tra dữ liệu trên topic"""
    try:
        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            consumer_timeout_ms=5000,  # Timeout sau 5 giây
            value_deserializer=lambda x: x.decode('utf-8')
        )
        
        print(f"🔍 Đang kiểm tra topic: {topic_name}")
        print("=" * 60)
        
        message_count = 0
        for message in consumer:
            message_count += 1
            print(f"\n📨 Message #{message_count}:")
            print(f"   Partition: {message.partition}")
            print(f"   Offset: {message.offset}")
            print(f"   Value: {message.value}")
            
            # Parse JSON nếu có thể
            try:
                data = json.loads(message.value)
                print(f"   Parsed JSON:")
                for key, value in data.items():
                    print(f"      {key}: {value}")
            except:
                pass
            
            if message_count >= max_messages:
                break
        
        if message_count == 0:
            print(f"⚠️  Không có dữ liệu nào trên topic {topic_name}")
            print("   Có thể:")
            print("   - Spark chưa xử lý dữ liệu")
            print("   - Máy 1 chưa gửi dữ liệu lên parking-raw-events")
            print("   - Spark đang chờ dữ liệu mới")
        else:
            print(f"\n✅ Tìm thấy {message_count} message(s) trên topic {topic_name}")
        
        consumer.close()
        return message_count
        
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra topic: {e}")
        return 0

if __name__ == "__main__":
    topic = "parking-processed-results"
    max_msgs = 10
    
    if len(sys.argv) > 1:
        max_msgs = int(sys.argv[1])
    
    count = check_topic(topic, max_msgs)
    sys.exit(0 if count > 0 else 1)

