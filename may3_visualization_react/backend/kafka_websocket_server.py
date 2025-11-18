#!/usr/bin/env python3
"""
Backend WebSocket server để stream data từ Kafka đến React frontend
Hỗ trợ cả local mode (1 máy) và distributed mode (nhiều máy)
"""

import json
import re
import math
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load config từ file
def load_config():
    """Load cấu hình từ config.json"""
    config_path = Path(__file__).parent.parent / 'config.json'
    
    # Fallback về config.local.json nếu không tìm thấy config.json
    if not config_path.exists():
        config_path = Path(__file__).parent.parent / 'config.local.json'
        logger.warning(f"Không tìm thấy config.json, sử dụng config.local.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"✅ Đã load config từ {config_path}")
        logger.info(f"   Mode: {config.get('mode', 'unknown')}")
        return config
    except Exception as e:
        logger.error(f"❌ Lỗi load config: {e}")
        logger.info("Sử dụng cấu hình mặc định (localhost)")
        return {
            'mode': 'local',
            'backend': {
                'kafka': {
                    'bootstrap_servers': 'localhost:9092',
                    'topic': 'parking-processed-results'
                },
                'websocket': {
                    'host': '0.0.0.0',
                    'port': 5000
                }
            }
        }

# Load config
CONFIG = load_config()

# Khởi tạo Flask app và SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'parking-visualization-secret'
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# State management
parking_lot_map = {}  # {location: vehicle_info}
vehicle_details = {}  # {license_plate: details}
statistics = {
    'total_locations': 60,
    'occupied_count': 0,
    'available_count': 60,
    'total_revenue': 0,
    'messages_processed': 0
}

# Kafka consumer
consumer = None
consumer_thread = None
running = False

# Kafka config từ file config
KAFKA_BOOTSTRAP_SERVERS = CONFIG['backend']['kafka']['bootstrap_servers']
KAFKA_TOPIC = CONFIG['backend']['kafka']['topic']
WEBSOCKET_HOST = CONFIG['backend']['websocket']['host']
WEBSOCKET_PORT = CONFIG['backend']['websocket']['port']

logger.info(f"📋 Cấu hình Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
logger.info(f"📋 Topic: {KAFKA_TOPIC}")
logger.info(f"📋 WebSocket: {WEBSOCKET_HOST}:{WEBSOCKET_PORT}")


def parse_license_plate(license_plate_str):
    """Parse license plate từ format ('30B-55555',) thành 30B-55555"""
    if not license_plate_str:
        return ""
    # Remove tuple format
    match = re.search(r"['\"]([^'\"]+)['\"]", str(license_plate_str))
    if match:
        return match.group(1)
    return str(license_plate_str).strip("()',\"")


def calculate_realtime_cost(parked_start_time_str, current_time=None):
    """
    Tính tiền real-time dựa trên thời gian bắt đầu đỗ
    BLOCK_PRICE = 10000 VNĐ mỗi block 10 phút
    """
    if not parked_start_time_str:
        return 0, 0, 0
    
    try:
        # Parse thời gian bắt đầu đỗ
        if isinstance(parked_start_time_str, str):
            try:
                # Thử parse ISO format
                parked_start = datetime.fromisoformat(parked_start_time_str.replace('Z', '+00:00'))
                # Remove timezone info để so sánh
                if parked_start.tzinfo:
                    parked_start = parked_start.replace(tzinfo=None)
            except:
                # Fallback: parse format khác
                try:
                    parked_start = datetime.strptime(parked_start_time_str, "%Y-%m-%d %H:%M:%S")
                except:
                    parked_start = datetime.now()
        else:
            parked_start = parked_start_time_str
            if hasattr(parked_start, 'tzinfo') and parked_start.tzinfo:
                parked_start = parked_start.replace(tzinfo=None)
        
        # Thời gian hiện tại
        if current_time is None:
            current_time = datetime.now()
        
        # Tính duration
        duration_seconds = (current_time - parked_start).total_seconds()
        duration_minutes = duration_seconds / 60
        
        # Tính blocks (mỗi block = 10 phút, làm tròn lên)
        parked_blocks = math.ceil(duration_minutes / 10) if duration_minutes > 0 else 1
        
        # Tính cost
        BLOCK_PRICE = 10000
        total_cost = parked_blocks * BLOCK_PRICE
        
        return duration_minutes, parked_blocks, total_cost
    except Exception as e:
        logger.error(f"Lỗi tính tiền real-time: {e}")
        return 0, 0, 0


def process_message(data):
    """Xử lý message từ Kafka"""
    global parking_lot_map, vehicle_details, statistics
    
    try:
        event_type = data.get('event_type', 'vehicle_event')
        action = data.get('action', '')
        license_plate_raw = data.get('license_plate', '')
        license_plate = parse_license_plate(license_plate_raw)
        location = data.get('location', '')
        
        # Validate dữ liệu
        if not license_plate or not location:
            logger.warning(f"Message thiếu dữ liệu: {data}")
            return
        
        statistics['messages_processed'] += 1
        
        if event_type in ['vehicle_event', 'timer_event']:
            if action == 'vehicle_entered':
                # Xe mới vào
                current_time = datetime.now()
                parking_lot_map[location] = {
                    'license_plate': license_plate,
                    'status': 'ENTERING',
                    'parked_start_time': current_time.isoformat(),
                    'parked_duration_minutes': 0,
                    'parked_blocks': 0,
                    'total_cost': 0,
                    'last_update': current_time.isoformat()
                }
                vehicle_details[license_plate] = {
                    'location': location,
                    'status': 'ENTERING',
                    'parked_start_time': current_time.isoformat()
                }
                logger.info(f"Xe {license_plate} vào tại {location}")
            
            elif action in ['vehicle_parked', 'parking_updated', 'periodic_update']:
                # Xe đã đỗ hoặc cập nhật
                parked_duration = data.get('parked_duration_minutes', 0)
                parked_blocks = data.get('parked_blocks', 0)
                total_cost = data.get('total_cost', 0)
                
                # Lấy thời gian bắt đầu đỗ từ data hoặc từ state hiện tại
                timestamp_str = data.get('timestamp', '')
                if timestamp_str:
                    try:
                        if isinstance(timestamp_str, str):
                            try:
                                event_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                if event_time.tzinfo:
                                    event_time = event_time.replace(tzinfo=None)
                            except:
                                try:
                                    event_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                except:
                                    event_time = datetime.now()
                        else:
                            event_time = timestamp_str
                            if hasattr(event_time, 'tzinfo') and event_time.tzinfo:
                                event_time = event_time.replace(tzinfo=None)
                    except:
                        event_time = datetime.now()
                else:
                    event_time = datetime.now()
                
                # Nếu đã có trong map, giữ nguyên parked_start_time
                if location in parking_lot_map:
                    parked_start_time = parking_lot_map[location].get('parked_start_time', event_time.isoformat())
                else:
                    parked_start_time = event_time.isoformat()
                
                parking_lot_map[location] = {
                    'license_plate': license_plate,
                    'status': 'PARKED',
                    'parked_start_time': parked_start_time,
                    'parked_duration_minutes': parked_duration,
                    'parked_blocks': parked_blocks,
                    'total_cost': total_cost,
                    'last_update': event_time.isoformat()
                }
                vehicle_details[license_plate] = {
                    'location': location,
                    'status': 'PARKED',
                    'parked_start_time': parked_start_time,
                    'parked_duration_minutes': parked_duration,
                    'parked_blocks': parked_blocks,
                    'total_cost': total_cost
                }
                logger.debug(f"Cập nhật: {license_plate} tại {location} - {parked_duration:.1f} phút - {total_cost:,} VNĐ")
            
            elif action == 'vehicle_exiting':
                # Xe đang ra - tính tiền cuối cùng
                if location in parking_lot_map:
                    vehicle_info = parking_lot_map[location]
                    license_plate_exit = vehicle_info.get('license_plate', '')
                    parked_start_time = vehicle_info.get('parked_start_time', '')
                    
                    # Tính tiền cuối cùng
                    final_duration, final_blocks, final_cost = calculate_realtime_cost(parked_start_time)
                    
                    # Gửi thông tin xe ra với tiền cuối cùng
                    exit_info = {
                        'license_plate': license_plate_exit,
                        'location': location,
                        'final_duration_minutes': final_duration,
                        'final_blocks': final_blocks,
                        'final_cost': final_cost
                    }
                    
                    del parking_lot_map[location]
                    if license_plate_exit in vehicle_details:
                        del vehicle_details[license_plate_exit]
                    
                    logger.info(f"Xe {license_plate_exit} ra khỏi {location} - Tiền: {final_cost:,} VNĐ")
                    
                    # Emit event xe ra
                    socketio.emit('vehicle_exited', exit_info)
        
        # Cập nhật thống kê
        update_statistics()
        
        # Broadcast update đến tất cả clients
        broadcast_update()
        
    except Exception as e:
        logger.error(f"Lỗi xử lý message: {e}")


def update_statistics():
    """Cập nhật thống kê"""
    global statistics, parking_lot_map
    
    statistics['occupied_count'] = len(parking_lot_map)
    statistics['available_count'] = statistics['total_locations'] - statistics['occupied_count']
    
    # Tính tổng doanh thu từ các xe đang đỗ (real-time)
    total_revenue = 0
    current_time = datetime.now()
    for location, vehicle_info in parking_lot_map.items():
        if vehicle_info.get('status') == 'PARKED':
            parked_start_time = vehicle_info.get('parked_start_time', '')
            _, _, cost = calculate_realtime_cost(parked_start_time, current_time)
            total_revenue += cost
    
    statistics['total_revenue'] = total_revenue


def broadcast_update():
    """Broadcast update đến tất cả clients"""
    global parking_lot_map, statistics
    
    # Tính lại cost real-time cho tất cả xe đang đỗ
    current_time = datetime.now()
    parking_map_with_realtime = {}
    
    for location, vehicle_info in parking_lot_map.items():
        vehicle_info_copy = vehicle_info.copy()
        
        if vehicle_info.get('status') == 'PARKED':
            parked_start_time = vehicle_info.get('parked_start_time', '')
            duration, blocks, cost = calculate_realtime_cost(parked_start_time, current_time)
            vehicle_info_copy['parked_duration_minutes'] = duration
            vehicle_info_copy['parked_blocks'] = blocks
            vehicle_info_copy['total_cost'] = cost
        
        parking_map_with_realtime[location] = vehicle_info_copy
    
    # Emit update
    socketio.emit('parking_update', {
        'parking_lot_map': parking_map_with_realtime,
        'statistics': statistics
    })


def kafka_consumer_loop():
    """Vòng lặp đọc messages từ Kafka"""
    global consumer, running
    
    while running:
        try:
            if consumer is None:
                consumer = KafkaConsumer(
                    KAFKA_TOPIC,
                    bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    consumer_timeout_ms=1000,
                    auto_offset_reset='latest',
                    enable_auto_commit=True,
                    group_id='parking-visualization-websocket'
                )
                logger.info(f"Đã kết nối đến Kafka: {KAFKA_BOOTSTRAP_SERVERS}, Topic: {KAFKA_TOPIC}")
            
            # Poll messages
            messages = consumer.poll(timeout_ms=1000)
            
            for topic_partition, message_list in messages.items():
                for message in message_list:
                    data = message.value if isinstance(message.value, dict) else json.loads(message.value)
                    process_message(data)
        
        except Exception as e:
            error_msg = str(e)
            if "wakeup" in error_msg.lower():
                logger.debug(f"Consumer đang đóng: {e}")
                break
            elif isinstance(e, KafkaError):
                logger.error(f"Lỗi Kafka: {e}")
                try:
                    if consumer:
                        consumer.close()
                except:
                    pass
                consumer = None
                time.sleep(5)
            else:
                logger.error(f"Lỗi không mong đợi: {e}")
                time.sleep(1)
    
    # Cleanup
    try:
        if consumer:
            consumer.close()
    except Exception as e:
        logger.debug(f"Lỗi khi đóng consumer: {e}")
    finally:
        consumer = None


def start_kafka_consumer():
    """Khởi động Kafka consumer thread"""
    global consumer_thread, running
    
    if consumer_thread and consumer_thread.is_alive():
        return
    
    running = True
    consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
    consumer_thread.start()
    logger.info("Đã khởi động Kafka consumer thread")


def stop_kafka_consumer():
    """Dừng Kafka consumer"""
    global running, consumer
    
    running = False
    
    if consumer:
        try:
            consumer.wakeup()
        except:
            pass
        try:
            consumer.close()
        except:
            pass
        consumer = None
    
    logger.info("Đã dừng Kafka consumer")


# SocketIO events
@socketio.on('connect')
def handle_connect():
    """Client kết nối"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'ok'})
    
    # Gửi state hiện tại
    current_time = datetime.now()
    parking_map_with_realtime = {}
    
    for location, vehicle_info in parking_lot_map.items():
        vehicle_info_copy = vehicle_info.copy()
        
        if vehicle_info.get('status') == 'PARKED':
            parked_start_time = vehicle_info.get('parked_start_time', '')
            duration, blocks, cost = calculate_realtime_cost(parked_start_time, current_time)
            vehicle_info_copy['parked_duration_minutes'] = duration
            vehicle_info_copy['parked_blocks'] = blocks
            vehicle_info_copy['total_cost'] = cost
        
        parking_map_with_realtime[location] = vehicle_info_copy
    
    emit('initial_state', {
        'parking_lot_map': parking_map_with_realtime,
        'statistics': statistics
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Client ngắt kết nối"""
    logger.info(f"Client disconnected: {request.sid}")


@socketio.on('request_update')
def handle_request_update():
    """Client yêu cầu update"""
    broadcast_update()


# HTTP routes
@app.route('/')
def index():
    """Health check"""
    return {'status': 'ok', 'service': 'parking-visualization-websocket'}


@app.route('/api/statistics')
def get_statistics():
    """API lấy thống kê"""
    update_statistics()
    return statistics


@app.route('/api/parking-map')
def get_parking_map():
    """API lấy bản đồ bãi đỗ"""
    current_time = datetime.now()
    parking_map_with_realtime = {}
    
    for location, vehicle_info in parking_lot_map.items():
        vehicle_info_copy = vehicle_info.copy()
        
        if vehicle_info.get('status') == 'PARKED':
            parked_start_time = vehicle_info.get('parked_start_time', '')
            duration, blocks, cost = calculate_realtime_cost(parked_start_time, current_time)
            vehicle_info_copy['parked_duration_minutes'] = duration
            vehicle_info_copy['parked_blocks'] = blocks
            vehicle_info_copy['total_cost'] = cost
        
        parking_map_with_realtime[location] = vehicle_info_copy
    
    return {
        'parking_lot_map': parking_map_with_realtime,
        'statistics': statistics
    }


if __name__ == '__main__':
    # Khởi động Kafka consumer
    start_kafka_consumer()
    
    # Khởi động periodic update (mỗi 2 giây để tính tiền real-time)
    def periodic_update():
        while running:
            time.sleep(2)
            if running:
                update_statistics()
                broadcast_update()
    
    update_thread = threading.Thread(target=periodic_update, daemon=True)
    update_thread.start()
    
    # Chạy Flask-SocketIO server
    logger.info(f"🚀 Khởi động WebSocket server trên http://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    logger.info(f"   Mode: {CONFIG.get('mode', 'unknown')}")
    socketio.run(app, host=WEBSOCKET_HOST, port=WEBSOCKET_PORT, debug=False, use_reloader=False)

