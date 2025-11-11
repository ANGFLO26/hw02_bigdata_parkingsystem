from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import *
from pyspark.sql.streaming.state import StatefulProcessor, StatefulProcessorHandle
import pandas as pd
from datetime import datetime
import math

# Giá mỗi block 10 phút (VNĐ)
BLOCK_PRICE = 10000

# Schema cho input từ Kafka
input_schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("timestamp_unix", LongType(), True),
    StructField("license_plate", StringType(), True),
    StructField("location", StringType(), True),
    StructField("status_code", StringType(), True)
])

# Schema cho state của mỗi xe
vehicle_state_schema = StructType([
    StructField("license_plate", StringType(), True),
    StructField("location", StringType(), True),
    StructField("status", StringType(), True),
    StructField("parked_start_time", TimestampType(), True),
    StructField("last_update_time", TimestampType(), True),
    StructField("parked_blocks", IntegerType(), True),
    StructField("total_cost", LongType(), True)
])

# Schema cho output
output_schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("timestamp_unix", LongType(), True),
    StructField("license_plate", StringType(), True),
    StructField("location", StringType(), True),
    StructField("status", StringType(), True),
    StructField("action", StringType(), True),
    StructField("parked_duration_minutes", DoubleType(), True),
    StructField("parked_blocks", IntegerType(), True),
    StructField("total_cost", LongType(), True),
    StructField("event_type", StringType(), True)
])

class ParkingStateProcessor(StatefulProcessor):
    """StatefulProcessor để xử lý trạng thái đỗ xe"""
    
    def init(self, handle: StatefulProcessorHandle) -> None:
        """Khởi tạo state"""
        self.handle = handle
        self.vehicle_state = handle.getValueState("vehicle_state", vehicle_state_schema)
        self.BLOCK_PRICE = BLOCK_PRICE
    
    def handleInputRows(self, key, rows, timerValues) -> pd.DataFrame:
        """
        Xử lý các events đầu vào cho một license_plate
        
        Args:
            key: license_plate
            rows: List các pandas DataFrame chứa events
            timerValues: Thông tin về timers
        """
        # Chuyển rows thành list và tìm event mới nhất
        events = []
        for pdf in rows:
            for _, row in pdf.iterrows():
                events.append({
                    'timestamp': row['timestamp'],
                    'timestamp_unix': row['timestamp_unix'],
                    'license_plate': row['license_plate'],
                    'location': row['location'],
                    'status_code': row['status_code']
                })
        
        if not events:
            return pd.DataFrame()
        
        # Lấy event mới nhất (theo timestamp_unix)
        latest_event = max(events, key=lambda x: x['timestamp_unix'])
        
        # Parse timestamp
        try:
            event_timestamp = datetime.fromtimestamp(latest_event['timestamp_unix'])
        except:
            event_timestamp = datetime.strptime(latest_event['timestamp'], "%Y-%m-%d %H:%M:%S")
        
        # Lấy state hiện tại
        current_state = None
        if self.vehicle_state.exists():
            state_data = self.vehicle_state.get()
            current_state = {
                'license_plate': state_data[0],
                'location': state_data[1],
                'status': state_data[2],
                'parked_start_time': state_data[3],
                'last_update_time': state_data[4],
                'parked_blocks': state_data[5],
                'total_cost': state_data[6]
            }
        
        # Xử lý theo status_code
        output_rows = []
        
        if latest_event['status_code'] == 'ENTERING':
            # Xe mới vào
            if current_state is None or current_state['status'] == 'EXITING':
                # Tạo state mới
                new_state = (
                    key,
                    latest_event['location'],
                    'ENTERING',
                    None,  # parked_start_time
                    event_timestamp,
                    0,  # parked_blocks
                    0   # total_cost
                )
                self.vehicle_state.update(new_state)
                
                output_rows.append({
                    'timestamp': latest_event['timestamp'],
                    'timestamp_unix': latest_event['timestamp_unix'],
                    'license_plate': key,
                    'location': latest_event['location'],
                    'status': 'ENTERING',
                    'action': 'vehicle_entered',
                    'parked_duration_minutes': 0.0,
                    'parked_blocks': 0,
                    'total_cost': 0,
                    'event_type': 'vehicle_event'
                })
        
        elif latest_event['status_code'] == 'PARKED':
            # Xe đã đỗ
            if current_state is None or current_state['status'] != 'PARKED':
                # Lần đầu chuyển sang PARKED
                parked_start = event_timestamp
                new_state = (
                    key,
                    latest_event['location'],
                    'PARKED',
                    parked_start,
                    event_timestamp,
                    1,  # Block đầu tiên
                    self.BLOCK_PRICE
                )
                self.vehicle_state.update(new_state)
                
                output_rows.append({
                    'timestamp': latest_event['timestamp'],
                    'timestamp_unix': latest_event['timestamp_unix'],
                    'license_plate': key,
                    'location': latest_event['location'],
                    'status': 'PARKED',
                    'action': 'vehicle_parked',
                    'parked_duration_minutes': 0.0,
                    'parked_blocks': 1,
                    'total_cost': self.BLOCK_PRICE,
                    'event_type': 'vehicle_event'
                })
                
                # Đăng ký timer để cập nhật định kỳ (1 phút)
                current_time_ms = timerValues.getCurrentProcessingTimeInMs()
                self.handle.registerTimer(current_time_ms + 60000)
                
            else:
                # Xe đã đỗ, cập nhật thời gian
                if current_state['parked_start_time']:
                    parked_start = current_state['parked_start_time']
                    parked_duration_minutes = (event_timestamp - parked_start).total_seconds() / 60
                    parked_blocks = math.ceil(parked_duration_minutes / 10)
                    total_cost = parked_blocks * self.BLOCK_PRICE
                else:
                    # Trường hợp đặc biệt: state không có parked_start_time
                    parked_start = event_timestamp
                    parked_duration_minutes = 0.0
                    parked_blocks = 1
                    total_cost = self.BLOCK_PRICE
                
                new_state = (
                    key,
                    latest_event['location'],
                    'PARKED',
                    parked_start,
                    event_timestamp,
                    parked_blocks,
                    total_cost
                )
                self.vehicle_state.update(new_state)
                
                output_rows.append({
                    'timestamp': latest_event['timestamp'],
                    'timestamp_unix': latest_event['timestamp_unix'],
                    'license_plate': key,
                    'location': latest_event['location'],
                    'status': 'PARKED',
                    'action': 'parking_updated',
                    'parked_duration_minutes': parked_duration_minutes,
                    'parked_blocks': parked_blocks,
                    'total_cost': total_cost,
                    'event_type': 'vehicle_event'
                })
        
        elif latest_event['status_code'] == 'MOVING':
            # Xe đang di chuyển
            if current_state:
                # Giữ nguyên thông tin đỗ, chỉ cập nhật status
                new_state = (
                    key,
                    current_state['location'],
                    'MOVING',
                    current_state['parked_start_time'],
                    event_timestamp,
                    current_state['parked_blocks'],
                    current_state['total_cost']
                )
                self.vehicle_state.update(new_state)
                
                # Xóa timer cũ
                for timer in self.handle.listTimers():
                    self.handle.deleteTimer(timer)
                
                parked_duration = 0.0
                if current_state['parked_start_time']:
                    parked_duration = (event_timestamp - current_state['parked_start_time']).total_seconds() / 60
                
                output_rows.append({
                    'timestamp': latest_event['timestamp'],
                    'timestamp_unix': latest_event['timestamp_unix'],
                    'license_plate': key,
                    'location': latest_event['location'],
                    'status': 'MOVING',
                    'action': 'vehicle_moving',
                    'parked_duration_minutes': parked_duration,
                    'parked_blocks': current_state['parked_blocks'],
                    'total_cost': current_state['total_cost'],
                    'event_type': 'vehicle_event'
                })
        
        elif latest_event['status_code'] == 'EXITING':
            # Xe đang ra
            if current_state:
                # Tính tiền cuối cùng (nếu đã đỗ)
                parked_duration_minutes = 0.0
                parked_blocks = 0
                final_cost = 0
                
                if current_state['parked_start_time']:
                    parked_start = current_state['parked_start_time']
                    parked_duration_minutes = (event_timestamp - parked_start).total_seconds() / 60
                    parked_blocks = math.ceil(parked_duration_minutes / 10)
                    final_cost = parked_blocks * self.BLOCK_PRICE
                else:
                    # Xe chưa đỗ nhưng đã ra (có thể là lỗi hoặc xe vào rồi ra ngay)
                    parked_blocks = current_state.get('parked_blocks', 0)
                    final_cost = current_state.get('total_cost', 0)
                
                output_rows.append({
                    'timestamp': latest_event['timestamp'],
                    'timestamp_unix': latest_event['timestamp_unix'],
                    'license_plate': key,
                    'location': latest_event['location'],
                    'status': 'EXITING',
                    'action': 'vehicle_exiting',
                    'parked_duration_minutes': parked_duration_minutes,
                    'parked_blocks': parked_blocks,
                    'total_cost': final_cost,
                    'event_type': 'vehicle_event'
                })
                
                # Xóa timer và state
                for timer in self.handle.listTimers():
                    self.handle.deleteTimer(timer)
                self.vehicle_state.delete()
        
        if output_rows:
            return pd.DataFrame(output_rows)
        return pd.DataFrame()
    
    def handleExpiredTimer(self, key, timerValues, expiredTimerInfo) -> pd.DataFrame:
        """
        Xử lý khi timer hết hạn - cập nhật định kỳ cho xe đang đỗ
        """
        if not self.vehicle_state.exists():
            return pd.DataFrame()
        
        state_data = self.vehicle_state.get()
        current_state = {
            'license_plate': state_data[0],
            'location': state_data[1],
            'status': state_data[2],
            'parked_start_time': state_data[3],
            'last_update_time': state_data[4],
            'parked_blocks': state_data[5],
            'total_cost': state_data[6]
        }
        
        if current_state['status'] != 'PARKED':
            return pd.DataFrame()
        
        # Tính lại thời gian đỗ từ parked_start_time đến hiện tại
        current_time_ms = timerValues.getCurrentProcessingTimeInMs()
        current_time = datetime.fromtimestamp(current_time_ms / 1000)
        parked_start = current_state['parked_start_time']
        
        parked_duration_minutes = (current_time - parked_start).total_seconds() / 60
        parked_blocks = math.ceil(parked_duration_minutes / 10)
        total_cost = parked_blocks * self.BLOCK_PRICE
        
        # Cập nhật state
        updated_state = (
            key,
            current_state['location'],
            'PARKED',
            parked_start,
            current_time,
            parked_blocks,
            total_cost
        )
        self.vehicle_state.update(updated_state)
        
        # Emit cập nhật định kỳ
        output_row = {
            'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
            'timestamp_unix': int(current_time_ms / 1000),
            'license_plate': key,
            'location': current_state['location'],
            'status': 'PARKED',
            'action': 'periodic_update',
            'parked_duration_minutes': parked_duration_minutes,
            'parked_blocks': parked_blocks,
            'total_cost': total_cost,
            'event_type': 'timer_event'
        }
        
        # Đăng ký timer tiếp theo (1 phút sau)
        self.handle.registerTimer(current_time_ms + 60000)
        
        return pd.DataFrame([output_row])
    
    def close(self) -> None:
        """Cleanup khi đóng processor"""
        pass

def create_spark_session(checkpoint_location=None):
    """Tạo SparkSession với cấu hình phù hợp"""
    builder = SparkSession.builder \
        .appName("ParkingStatefulProcessor") \
        .config("spark.sql.streaming.stateStore.providerClass", "org.apache.spark.sql.execution.streaming.state.HDFSBackedStateStoreProvider") \
        .config("spark.sql.streaming.stateStore.maintenanceInterval", "60s")
    
    # Cấu hình checkpoint location
    if checkpoint_location:
        builder = builder.config("spark.sql.streaming.checkpointLocation", checkpoint_location)
    else:
        builder = builder.config("spark.sql.streaming.checkpointLocation", "/tmp/parking-checkpoint")
    
    spark = builder.getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    return spark

def main():
    """Hàm main để chạy Spark streaming"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Spark Stateful Processing cho bãi đỗ xe')
    parser.add_argument('--kafka-bootstrap', type=str, default='localhost:9092',
                       help='Địa chỉ Kafka bootstrap servers (default: localhost:9092)')
    parser.add_argument('--input-topic', type=str, default='parking-raw-events',
                       help='Tên Kafka input topic (default: parking-raw-events)')
    parser.add_argument('--output-topic', type=str, default='parking-processed-results',
                       help='Tên Kafka output topic (default: parking-processed-results)')
    parser.add_argument('--checkpoint', type=str, default='/tmp/parking-checkpoint',
                       help='Đường dẫn checkpoint (default: /tmp/parking-checkpoint)')
    
    args = parser.parse_args()
    
    # Tạo SparkSession với checkpoint location
    spark = create_spark_session(checkpoint_location=args.checkpoint)
    
    # Đọc từ Kafka
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", args.kafka_bootstrap) \
        .option("subscribe", args.input_topic) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    # Parse JSON và filter null values
    df_parsed = df.select(
        from_json(col("value").cast("string"), input_schema).alias("data")
    ).select("data.*").filter(
        col("license_plate").isNotNull() & 
        col("location").isNotNull() & 
        col("status_code").isNotNull()
    )
    
    # Áp dụng watermark
    df_with_watermark = df_parsed.withWatermark("timestamp_unix", "10 minutes")
    
    # Group by license_plate và áp dụng StatefulProcessor
    result_df = df_with_watermark \
        .groupBy("license_plate") \
        .transformWithStateInPandas(
            statefulProcessor=ParkingStateProcessor(),
            outputStructType=output_schema,
            outputMode="Update",
            timeMode="ProcessingTime"
        )
    
    # Ghi kết quả lên Kafka
    query = result_df \
        .select(to_json(struct("*")).alias("value")) \
        .writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", args.kafka_bootstrap) \
        .option("topic", args.output_topic) \
        .option("checkpointLocation", args.checkpoint) \
        .outputMode("update") \
        .start()
    
    print("Spark streaming đã bắt đầu...")
    print(f"Đọc từ topic: {args.input_topic}")
    print(f"Ghi vào topic: {args.output_topic}")
    
    query.awaitTermination()

if __name__ == "__main__":
    main()

