import json
import threading
import time
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import logging
import streamlit as st
import pandas as pd

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Khởi tạo session state
if 'parking_lot_map' not in st.session_state:
    st.session_state.parking_lot_map = {}
if 'vehicle_details' not in st.session_state:
    st.session_state.vehicle_details = {}
if 'statistics' not in st.session_state:
    st.session_state.statistics = {
        'total_locations': 60,
        'occupied_count': 0,
        'available_count': 60,
        'total_revenue': 0
    }
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "Đang kết nối..."
if 'consumer' not in st.session_state:
    st.session_state.consumer = None
if 'consumer_thread' not in st.session_state:
    st.session_state.consumer_thread = None
if 'running' not in st.session_state:
    st.session_state.running = False

# Tất cả vị trí
ALL_LOCATIONS = []
for floor in ['A', 'B', 'C', 'D', 'E', 'F']:
    for num in range(1, 11):
        ALL_LOCATIONS.append(f"{floor}{num}")

def connect_kafka(kafka_bootstrap_servers, kafka_topic):
    """Kết nối đến Kafka"""
    try:
        consumer = KafkaConsumer(
            kafka_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            consumer_timeout_ms=1000,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='parking-visualization-streamlit'
        )
        logger.info(f"Đã kết nối đến Kafka: {kafka_bootstrap_servers}")
        st.session_state.connection_status = "✅ Đã kết nối"
        return consumer
    except Exception as e:
        logger.error(f"Lỗi kết nối Kafka: {e}")
        st.session_state.connection_status = "❌ Lỗi kết nối"
        return None

def process_message(data):
    """Xử lý message từ Kafka"""
    try:
        event_type = data.get('event_type', 'vehicle_event')
        action = data.get('action', '')
        license_plate = data.get('license_plate', '')
        location = data.get('location', '')
        
        # Validate dữ liệu cần thiết
        if not license_plate or not location:
            logger.warning(f"Message thiếu dữ liệu: {data}")
            return
        
        if event_type == 'vehicle_event' or event_type == 'timer_event':
            if action == 'vehicle_entered':
                # Xe mới vào
                st.session_state.parking_lot_map[location] = {
                    'license_plate': license_plate,
                    'status': 'ENTERING',
                    'parked_duration_minutes': 0,
                    'parked_blocks': 0,
                    'total_cost': 0
                }
                st.session_state.vehicle_details[license_plate] = {
                    'location': location,
                    'status': 'ENTERING'
                }
            
            elif action in ['vehicle_parked', 'parking_updated', 'periodic_update']:
                # Xe đã đỗ hoặc cập nhật
                parked_duration = data.get('parked_duration_minutes', 0)
                parked_blocks = data.get('parked_blocks', 0)
                total_cost = data.get('total_cost', 0)
                
                st.session_state.parking_lot_map[location] = {
                    'license_plate': license_plate,
                    'status': 'PARKED',
                    'parked_duration_minutes': parked_duration,
                    'parked_blocks': parked_blocks,
                    'total_cost': total_cost
                }
                st.session_state.vehicle_details[license_plate] = {
                    'location': location,
                    'status': 'PARKED',
                    'parked_duration_minutes': parked_duration,
                    'parked_blocks': parked_blocks,
                    'total_cost': total_cost
                }
            
            elif action == 'vehicle_exiting':
                # Xe đang ra
                if location in st.session_state.parking_lot_map:
                    del st.session_state.parking_lot_map[location]
                if license_plate in st.session_state.vehicle_details:
                    del st.session_state.vehicle_details[license_plate]
        
        # Cập nhật thống kê
        update_statistics()
        
    except Exception as e:
        logger.error(f"Lỗi xử lý message: {e}")

def update_statistics():
    """Cập nhật thống kê"""
    st.session_state.statistics['occupied_count'] = len(st.session_state.parking_lot_map)
    st.session_state.statistics['available_count'] = st.session_state.statistics['total_locations'] - st.session_state.statistics['occupied_count']
    st.session_state.statistics['total_revenue'] = sum(
        v.get('total_cost', 0) for v in st.session_state.parking_lot_map.values()
    )

def kafka_consumer_loop(kafka_bootstrap_servers, kafka_topic):
    """Vòng lặp đọc messages từ Kafka"""
    while st.session_state.running:
        try:
            if st.session_state.consumer is None:
                st.session_state.consumer = connect_kafka(kafka_bootstrap_servers, kafka_topic)
                if st.session_state.consumer is None:
                    time.sleep(5)
                    continue
            
            # Poll messages
            messages = st.session_state.consumer.poll(timeout_ms=1000)
            
            for topic_partition, message_list in messages.items():
                for message in message_list:
                    data = message.value if isinstance(message.value, dict) else json.loads(message.value)
                    process_message(data)
            
        except Exception as e:
            error_msg = str(e)
            # Bỏ qua lỗi wakeup socket khi đang đóng consumer
            if "wakeup" in error_msg.lower() or "wakeup" in str(type(e)).lower():
                logger.debug(f"Consumer đang đóng: {e}")
                break
            elif isinstance(e, KafkaError):
                logger.error(f"Lỗi Kafka: {e}")
                st.session_state.connection_status = "❌ Lỗi kết nối"
                try:
                    if st.session_state.consumer:
                        st.session_state.consumer.close()
                except:
                    pass
                st.session_state.consumer = None
                time.sleep(5)
            else:
                logger.error(f"Lỗi không mong đợi: {e}")
                time.sleep(1)
    
    # Cleanup khi thoát loop
    try:
        if st.session_state.consumer:
            st.session_state.consumer.close()
    except Exception as e:
        logger.debug(f"Lỗi khi đóng consumer: {e}")
    finally:
        st.session_state.consumer = None

def create_parking_map():
    """Tạo bản đồ bãi đỗ xe"""
    # Chia thành các tầng
    floors = ['A', 'B', 'C', 'D', 'E', 'F']
    
    for floor in floors:
        st.subheader(f"Tầng {floor}")
        cols = st.columns(10)
        
        for i in range(10):
            location = f"{floor}{i+1}"
            with cols[i]:
                if location in st.session_state.parking_lot_map:
                    vehicle_info = st.session_state.parking_lot_map[location]
                    license_plate = vehicle_info.get('license_plate', 'N/A')
                    parked_duration = vehicle_info.get('parked_duration_minutes', 0)
                    total_cost = vehicle_info.get('total_cost', 0)
                    
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #ff6b6b;
                            color: white;
                            padding: 10px;
                            border-radius: 5px;
                            text-align: center;
                            font-weight: bold;
                            margin-bottom: 5px;
                        ">
                            {location}<br>
                            {license_plate}<br>
                            <small>{parked_duration:.1f} phút</small><br>
                            <small>{total_cost:,} đ</small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #51cf66;
                            color: white;
                            padding: 10px;
                            border-radius: 5px;
                            text-align: center;
                            font-weight: bold;
                            margin-bottom: 5px;
                        ">
                            {location}<br>
                            TRỐNG
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

def main():
    """Hàm main Streamlit"""
    st.set_page_config(
        page_title="Bãi Đỗ Xe - Dashboard Real-time",
        page_icon="🚗",
        layout="wide"
    )
    
    st.title("🚗 Bãi Đỗ Xe - Dashboard Real-time")
    
    # Sidebar để cấu hình
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        kafka_bootstrap = st.text_input(
            "Kafka Bootstrap Servers",
            value="localhost:9092",
            help="Địa chỉ Kafka broker (ví dụ: localhost:9092 hoặc 192.168.1.100:9092)"
        )
        kafka_topic = st.text_input(
            "Kafka Topic",
            value="parking-processed-results",
            help="Tên Kafka topic để đọc dữ liệu"
        )
        
        if st.button("🔄 Kết nối/Khởi động lại"):
            # Dừng consumer cũ trước
            st.session_state.running = False
            if st.session_state.consumer:
                try:
                    st.session_state.consumer.wakeup()
                except:
                    pass
                try:
                    st.session_state.consumer.close()
                except:
                    pass
            st.session_state.consumer = None
            # Đợi thread cũ kết thúc
            if st.session_state.consumer_thread and st.session_state.consumer_thread.is_alive():
                st.session_state.consumer_thread.join(timeout=2)
            st.session_state.consumer_thread = None
            
            # Khởi động lại
            st.session_state.running = True
            st.session_state.consumer = connect_kafka(kafka_bootstrap, kafka_topic)
            if st.session_state.consumer:
                # Khởi động consumer thread nếu chưa chạy
                if st.session_state.consumer_thread is None or not st.session_state.consumer_thread.is_alive():
                    consumer_thread = threading.Thread(
                        target=kafka_consumer_loop,
                        args=(kafka_bootstrap, kafka_topic),
                        daemon=True
                    )
                    consumer_thread.start()
                    st.session_state.consumer_thread = consumer_thread
            st.rerun()
        
        if st.button("⏹️ Dừng"):
            st.session_state.running = False
            if st.session_state.consumer:
                try:
                    st.session_state.consumer.wakeup()
                except:
                    pass
                try:
                    st.session_state.consumer.close()
                except:
                    pass
                st.session_state.consumer = None
            if st.session_state.consumer_thread and st.session_state.consumer_thread.is_alive():
                st.session_state.consumer_thread.join(timeout=2)
            st.session_state.consumer_thread = None
            st.rerun()
        
        st.divider()
        st.markdown(f"**Trạng thái:** {st.session_state.connection_status}")
    
    # Khởi động consumer nếu chưa chạy
    if st.session_state.running and st.session_state.consumer is None:
        st.session_state.consumer = connect_kafka(kafka_bootstrap, kafka_topic)
        if st.session_state.consumer:
            if st.session_state.consumer_thread is None or not st.session_state.consumer_thread.is_alive():
                consumer_thread = threading.Thread(
                    target=kafka_consumer_loop,
                    args=(kafka_bootstrap, kafka_topic),
                    daemon=True
                )
                consumer_thread.start()
                st.session_state.consumer_thread = consumer_thread
    
    # Cleanup khi app đóng
    if not st.session_state.running and st.session_state.consumer:
        try:
            st.session_state.consumer.wakeup()
        except:
            pass
        try:
            st.session_state.consumer.close()
        except:
            pass
        st.session_state.consumer = None
    
    # Cập nhật thống kê
    update_statistics()
    
    # Hiển thị thống kê
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Tổng số chỗ",
            st.session_state.statistics['total_locations']
        )
    
    with col2:
        st.metric(
            "Đã đỗ",
            st.session_state.statistics['occupied_count'],
            delta=f"{st.session_state.statistics['available_count']} trống"
        )
    
    with col3:
        st.metric(
            "Trống",
            st.session_state.statistics['available_count']
        )
    
    with col4:
        st.metric(
            "Doanh thu hiện tại",
            f"{st.session_state.statistics['total_revenue']:,} VNĐ"
        )
    
    st.divider()
    
    # Layout chính: Bản đồ và Bảng chi tiết
    col_map, col_table = st.columns([2, 1])
    
    with col_map:
        st.header("🗺️ Bản Đồ Bãi Xe")
        create_parking_map()
    
    with col_table:
        st.header("📊 Chi Tiết Xe Đang Đỗ")
        
        if st.session_state.parking_lot_map:
            # Tạo DataFrame từ parking_lot_map
            data = []
            for location, vehicle_info in sorted(st.session_state.parking_lot_map.items()):
                data.append({
                    'Vị trí': location,
                    'Biển số': vehicle_info.get('license_plate', 'N/A'),
                    'Thời gian đỗ (phút)': f"{vehicle_info.get('parked_duration_minutes', 0):.1f}",
                    'Số block': vehicle_info.get('parked_blocks', 0),
                    'Tiền (VNĐ)': f"{vehicle_info.get('total_cost', 0):,}"
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có xe nào đang đỗ")
    
    # Auto-refresh mỗi 2 giây
    time.sleep(2)
    if st.session_state.running:
        st.rerun()

if __name__ == "__main__":
    main()
