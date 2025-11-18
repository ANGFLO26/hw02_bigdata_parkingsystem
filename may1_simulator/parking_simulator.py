import time
import random
import json
from datetime import datetime
from enum import Enum
from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ParkingStatus(Enum):
    """Các trạng thái của xe trong bãi đỗ"""
    ENTERING = "Đang vào"
    PARKED = "Đã đỗ"
    MOVING = "Đang di chuyển"
    EXITING = "Đang ra"

class ParkingEvent:
    """Class đại diện cho một sự kiện đỗ xe"""
    
    # Danh sách biển số xe có sẵn (mở rộng)
    LICENSE_PLATES = [
        "29A-12345", "29A-54321", "29A-67890", "29A-11111", "29A-99999",
        "30B-12345", "30B-67890", "30B-33333", "30B-88888", "30B-55555",
        "51C-11111", "51C-22222", "51C-44444", "51C-77777", "51C-12121",
        "59D-98765", "59D-45678", "59D-13579", "59D-24680", "59D-86420",
        "79D-99999", "79D-10101", "79D-20202", "79D-30303", "79D-40404",
        "92E-54321", "92E-65432", "92E-76543", "92E-87654", "92E-98765",
        "15F-88888", "15F-11122", "15F-33344", "15F-55566", "15F-77788",
        "43G-22222", "43G-12389", "43G-45612", "43G-78945", "43G-32165",
        "60H-10203", "60H-40506", "60H-70809", "60H-20406", "60H-50810"
    ]
    
    # Danh sách vị trí đỗ (mở rộng đến tầng F)
    PARKING_LOCATIONS = [
        # Tầng A
        "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10",
        # Tầng B
        "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10",
        # Tầng C
        "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10",
        # Tầng D
        "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10",
        # Tầng E
        "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "E10",
        # Tầng F (VIP)
        "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10"
    ]
    
    def __init__(self, occupied_locations=None, active_license_plates=None):
        # Chọn biển số chưa được sử dụng
        if active_license_plates:
            available_plates = [plate for plate in self.LICENSE_PLATES if plate not in active_license_plates]
            if available_plates:
                self.license_plate = random.choice(available_plates)
            else:
                # Nếu hết biển số, chọn random (trường hợp này không nên xảy ra)
                self.license_plate = random.choice(self.LICENSE_PLATES)
        else:
            self.license_plate = random.choice(self.LICENSE_PLATES)
        
        # Chọn vị trí còn trống
        if occupied_locations:
            available_locations = [loc for loc in self.PARKING_LOCATIONS if loc not in occupied_locations]
            if available_locations:
                self.location = random.choice(available_locations)
            else:
                # Nếu hết chỗ, chọn random (trường hợp này không nên xảy ra)
                self.location = random.choice(self.PARKING_LOCATIONS)
        else:
            self.location = random.choice(self.PARKING_LOCATIONS)
        
        self.status = ParkingStatus.ENTERING
        self.parked_count = 0
        self.parked_duration = 0
        
    def next_status(self, occupied_locations=None, active_license_plates=None):
        """Chuyển sang trạng thái tiếp theo theo logic"""
        if self.status == ParkingStatus.ENTERING:
            self.status = ParkingStatus.PARKED
            # Giảm parked_duration để xe nhanh chuyển trạng thái (3-10 events thay vì 20-200)
            self.parked_duration = random.randint(3, 10)
            self.parked_count = 0
            
        elif self.status == ParkingStatus.PARKED:
            self.parked_count += 1
            
            if self.parked_count >= self.parked_duration:
                self.status = ParkingStatus.MOVING
                
        elif self.status == ParkingStatus.MOVING:
            self.status = ParkingStatus.EXITING
            
        else:
            # Nếu đã ra, tạo xe mới với vị trí và biển số trống
            self.__init__(occupied_locations, active_license_plates)
    
    def get_event_info(self):
        """Lấy thông tin sự kiện dưới dạng dictionary"""
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_unix": int(time.time()),
            "license_plate": self.license_plate,
            "location": self.location,
            "status_code": self.status.name
        }

class ParkingSimulator:
    """Class quản lý simulator và gửi dữ liệu lên Kafka"""
    
    def __init__(self, kafka_bootstrap_servers, kafka_topic, duration_minutes=30, event_interval=3):
        """
        Khởi tạo simulator
        
        Args:
            kafka_bootstrap_servers: Địa chỉ Kafka broker (ví dụ: "192.168.1.100:9092")
            kafka_topic: Tên topic Kafka để gửi dữ liệu
            duration_minutes: Thời gian chạy simulator (phút)
            event_interval: Thời gian trung bình giữa các sự kiện (giây)
        """
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_topic = kafka_topic
        self.duration_minutes = duration_minutes
        self.event_interval = event_interval
        
        # Khởi tạo Kafka Producer
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Đợi tất cả replicas xác nhận
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info(f"Đã kết nối đến Kafka broker: {kafka_bootstrap_servers}")
        except Exception as e:
            logger.error(f"Lỗi kết nối Kafka: {e}")
            raise
        
        # Theo dõi các vị trí và biển số đang được sử dụng
        self.occupied_locations = set()
        self.active_license_plates = set()
        
        # Tạo nhiều xe ngẫu nhiên để mô phỏng bãi đỗ thực tế
        self.active_vehicles = []
        self.stats = {
            'total_events_sent': 0,
            'successful_sends': 0,
            'failed_sends': 0,
            'start_time': None
        }
    
    def initialize_vehicles(self, count=5):
        """Khởi tạo số lượng xe ban đầu"""
        for _ in range(count):
            vehicle = ParkingEvent(self.occupied_locations, self.active_license_plates)
            self.active_vehicles.append(vehicle)
            self.occupied_locations.add(vehicle.location)
            self.active_license_plates.add(vehicle.license_plate)
        logger.info(f"Đã khởi tạo {count} xe ban đầu")
    
    def send_event_to_kafka(self, event_data):
        """Gửi event lên Kafka"""
        try:
            # Key là license_plate để Spark có thể groupBy
            future = self.producer.send(
                self.kafka_topic,
                key=event_data['license_plate'],
                value=event_data
            )
            
            # Đợi kết quả (có thể bỏ qua nếu muốn async)
            record_metadata = future.get(timeout=10)
            
            self.stats['total_events_sent'] += 1
            self.stats['successful_sends'] += 1
            
            logger.debug(f"Đã gửi event: {event_data['license_plate']} - {event_data['status_code']} - {event_data['location']}")
            return True
            
        except KafkaError as e:
            self.stats['total_events_sent'] += 1
            self.stats['failed_sends'] += 1
            logger.error(f"Lỗi gửi event lên Kafka: {e}")
            return False
        except Exception as e:
            self.stats['total_events_sent'] += 1
            self.stats['failed_sends'] += 1
            logger.error(f"Lỗi không mong đợi: {e}")
            return False
    
    def run(self):
        """Chạy simulator"""
        start_time = time.time()
        end_time = start_time + (self.duration_minutes * 60)
        self.stats['start_time'] = datetime.now()
        
        # Khởi tạo xe ban đầu
        self.initialize_vehicles(5)
        
        logger.info(f"Bắt đầu simulator - Thời gian chạy: {self.duration_minutes} phút")
        
        try:
            while time.time() < end_time:
                # Chọn ngẫu nhiên một xe để cập nhật trạng thái
                if not self.active_vehicles:
                    logger.warning("Không còn xe nào, tạo xe mới")
                    self.initialize_vehicles(3)
                
                vehicle = random.choice(self.active_vehicles)
                
                # Lưu trạng thái, vị trí và biển số cũ
                old_status = vehicle.status
                old_location = vehicle.location
                old_license_plate = vehicle.license_plate
                
                # Lấy thông tin event hiện tại
                event_data = vehicle.get_event_info()
                
                # Gửi lên Kafka
                self.send_event_to_kafka(event_data)
                
                # Chuyển sang trạng thái tiếp theo
                vehicle.next_status(self.occupied_locations, self.active_license_plates)
                
                # Quản lý occupied_locations và active_license_plates
                if old_status == ParkingStatus.EXITING and vehicle.status == ParkingStatus.ENTERING:
                    # Xe tạo mới với vị trí và biển số mới
                    self.occupied_locations.discard(old_location)
                    self.occupied_locations.add(vehicle.location)
                    self.active_license_plates.discard(old_license_plate)
                    self.active_license_plates.add(vehicle.license_plate)
                elif vehicle.status == ParkingStatus.EXITING and old_status != ParkingStatus.EXITING:
                    # Xe vừa chuyển sang EXITING - giải phóng vị trí
                    self.occupied_locations.discard(vehicle.location)
                
                # Thêm xe mới ngẫu nhiên (mô phỏng xe mới vào bãi)
                if random.random() > 0.6 and len(self.active_vehicles) < 8:
                    # Chỉ thêm nếu còn chỗ trống VÀ còn biển số
                    if (len(self.occupied_locations) < len(ParkingEvent.PARKING_LOCATIONS) and 
                        len(self.active_license_plates) < len(ParkingEvent.LICENSE_PLATES)):
                        new_vehicle = ParkingEvent(self.occupied_locations, self.active_license_plates)
                        self.active_vehicles.append(new_vehicle)
                        self.occupied_locations.add(new_vehicle.location)
                        self.active_license_plates.add(new_vehicle.license_plate)
                        logger.info(f"Thêm xe mới: {new_vehicle.license_plate} tại {new_vehicle.location}")
                
                # Xóa xe đã ra khỏi bãi
                if random.random() > 0.5:
                    vehicles_to_remove = [v for v in self.active_vehicles if v.status == ParkingStatus.EXITING]
                    for v in vehicles_to_remove:
                        self.active_vehicles.remove(v)
                        self.occupied_locations.discard(v.location)
                        self.active_license_plates.discard(v.license_plate)
                        logger.info(f"Xóa xe đã ra: {v.license_plate}")
                
                # Đảm bảo luôn có ít nhất 3 xe
                while (len(self.active_vehicles) < 3 and 
                       len(self.occupied_locations) < len(ParkingEvent.PARKING_LOCATIONS) and
                       len(self.active_license_plates) < len(ParkingEvent.LICENSE_PLATES)):
                    new_vehicle = ParkingEvent(self.occupied_locations, self.active_license_plates)
                    self.active_vehicles.append(new_vehicle)
                    self.occupied_locations.add(new_vehicle.location)
                    self.active_license_plates.add(new_vehicle.license_plate)
                
                # Delay ngẫu nhiên giữa các sự kiện
                delay = random.uniform(self.event_interval * 0.5, self.event_interval * 1.5)
                time.sleep(delay)
                
                # In thống kê định kỳ
                if self.stats['total_events_sent'] % 20 == 0:
                    elapsed = time.time() - start_time
                    logger.info(f"Đã gửi {self.stats['total_events_sent']} events | "
                              f"Thành công: {self.stats['successful_sends']} | "
                              f"Thất bại: {self.stats['failed_sends']} | "
                              f"Xe đang hoạt động: {len(self.active_vehicles)} | "
                              f"Thời gian đã chạy: {elapsed:.1f}s")
        
        except KeyboardInterrupt:
            logger.info("Nhận tín hiệu dừng (Ctrl+C)")
        
        finally:
            # Đóng Kafka producer
            self.producer.close()
            
            # In thống kê cuối cùng
            elapsed = time.time() - start_time
            logger.info("=" * 60)
            logger.info("THỐNG KÊ CUỐI CÙNG:")
            logger.info(f"Tổng số events đã gửi: {self.stats['total_events_sent']}")
            logger.info(f"Thành công: {self.stats['successful_sends']}")
            logger.info(f"Thất bại: {self.stats['failed_sends']}")
            logger.info(f"Thời gian chạy: {elapsed:.1f} giây")
            if elapsed > 0:
                logger.info(f"Tốc độ trung bình: {self.stats['total_events_sent'] / elapsed * 60:.2f} events/phút")
            else:
                logger.info("Tốc độ trung bình: N/A")
            logger.info("=" * 60)

def main():
    """Hàm main để chạy simulator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Parking Simulator - Gửi dữ liệu lên Kafka')
    parser.add_argument('--kafka-bootstrap', type=str, default='localhost:9092',
                       help='Địa chỉ Kafka bootstrap servers (default: localhost:9092)')
    parser.add_argument('--topic', type=str, default='parking-raw-events',
                       help='Tên Kafka topic (default: parking-raw-events)')
    parser.add_argument('--duration', type=int, default=30,
                       help='Thời gian chạy simulator (phút, default: 30)')
    parser.add_argument('--interval', type=float, default=3.0,
                       help='Thời gian trung bình giữa các events (giây, default: 3.0)')
    
    args = parser.parse_args()
    
    # Tạo và chạy simulator
    simulator = ParkingSimulator(
        kafka_bootstrap_servers=args.kafka_bootstrap,
        kafka_topic=args.topic,
        duration_minutes=args.duration,
        event_interval=args.interval
    )
    
    simulator.run()

if __name__ == "__main__":
    main()

