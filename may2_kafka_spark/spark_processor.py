from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import *
from pyspark.sql.streaming.stateful_processor import StatefulProcessor, StatefulProcessorHandle
from typing import Iterator  # THÊM DÒNG NÀY
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
# Sửa timestamp thành TimestampType
output_schema = StructType([
    StructField("timestamp", TimestampType(), True),  # SỬA
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

def create_empty_dataframe() -> pd.DataFrame:
    """
    Tạo DataFrame rỗng với đúng schema cho output.
    
    Spark 4.0+ yêu cầu DataFrame rỗng phải có đúng schema với columns và dtypes được khai báo rõ ràng.
    Sử dụng dtype='string' cho strings và dtype='datetime64[ns]' cho timestamp.
    """
    return pd.DataFrame({
        'timestamp': pd.Series(dtype='datetime64[ns]'),  # Nếu dùng TimestampType
        'timestamp_unix': pd.Series(dtype='int64'),
        'license_plate': pd.Series(dtype='string'),
        'location': pd.Series(dtype='string'),
        'status': pd.Series(dtype='string'),
        'action': pd.Series(dtype='string'),
        'parked_duration_minutes': pd.Series(dtype='float64'),
        'parked_blocks': pd.Series(dtype='int64'),
        'total_cost': pd.Series(dtype='int64'),
        'event_type': pd.Series(dtype='string')
    })

class ParkingStateProcessor(StatefulProcessor):
    """StatefulProcessor để xử lý trạng thái đỗ xe"""
    
    def init(self, handle: StatefulProcessorHandle) -> None:
        """Khởi tạo state"""
        self.handle = handle
        self.vehicle_state = handle.getValueState("vehicle_state", vehicle_state_schema)
        self.BLOCK_PRICE = BLOCK_PRICE
    
    def handleInputRows(self, key, rows, timerValues) -> Iterator[pd.DataFrame]:  # SỬA -> Iterator[pd.DataFrame]
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
            return  # Không yield gì cả
        
        # Lấy event mới nhất (theo timestamp_unix) - sử dụng sorted thay vì max với key
        sorted_events = sorted(events, key=lambda x: x['timestamp_unix'])
        latest_event = sorted_events[-1] if sorted_events else events[0]
        
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
                    'timestamp': event_timestamp,  # SỬA: dùng datetime object
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
                    'timestamp': event_timestamp,  # SỬA: datetime
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
                    'timestamp': event_timestamp,  # SỬA: datetime
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
                    'timestamp': event_timestamp,  # SỬA: datetime
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
                    'timestamp': event_timestamp,  # SỬA: datetime
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
        
        # Trả về kết quả - đảm bảo luôn trả về DataFrame với đúng schema và dtypes
        if output_rows:
            # Tạo DataFrame từ output_rows
            df = pd.DataFrame(output_rows)
            
            # Đảm bảo tất cả các cột cần thiết có mặt
            required_columns = ['timestamp', 'timestamp_unix', 'license_plate', 'location', 
                              'status', 'action', 'parked_duration_minutes', 'parked_blocks', 
                              'total_cost', 'event_type']
            
            # Thêm các cột thiếu với giá trị mặc định
            for col in required_columns:
                if col not in df.columns:
                    if col in ['timestamp', 'license_plate', 'location', 'status', 'action', 'event_type']:
                        df[col] = ''
                    elif col == 'timestamp_unix':
                        df[col] = 0
                    elif col == 'parked_duration_minutes':
                        df[col] = 0.0
                    elif col in ['parked_blocks', 'total_cost']:
                        df[col] = 0
            
            # Convert và đảm bảo dtypes đúng - xử lý từng cột một cách cẩn thận
            # Đảm bảo không có None/NaN values trước khi convert
            
            # String columns: convert tất cả giá trị sang string, XÓA astype('object')
            string_cols = ['license_plate', 'location', 'status', 'action', 'event_type']
            for col in string_cols:
                if col in df.columns:
                    # Convert tất cả giá trị sang string (bao gồm None -> 'None')
                    df[col] = df[col].astype(str)
                    # Thay thế 'None' và 'nan' bằng empty string
                    df[col] = df[col].replace(['None', 'nan', 'NaN'], '')
                    # XÓA dòng astype('object') - giữ 'string' tự nhiên
            
            # Timestamp column: đảm bảo là datetime
            if 'timestamp' in df.columns:
                # Nếu timestamp là datetime object, đảm bảo dtype là datetime64[ns]
                if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                # Đảm bảo dtype là datetime64[ns]
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            # Numeric columns: convert sang đúng dtype với xử lý lỗi
            df['timestamp_unix'] = pd.to_numeric(df['timestamp_unix'], errors='coerce').fillna(0).astype('int64')
            df['parked_duration_minutes'] = pd.to_numeric(df['parked_duration_minutes'], errors='coerce').fillna(0.0).astype('float64')
            df['parked_blocks'] = pd.to_numeric(df['parked_blocks'], errors='coerce').fillna(0).astype('int64')
            df['total_cost'] = pd.to_numeric(df['total_cost'], errors='coerce').fillna(0).astype('int64')
            
            # Đảm bảo thứ tự cột đúng và chỉ lấy các cột cần thiết
            result_df = df[required_columns].copy()
            
            # Reset index để đảm bảo DataFrame có index hợp lệ
            result_df = result_df.reset_index(drop=True)
            
            # Kiểm tra và đảm bảo không có None/NaN trong DataFrame
            # Thay thế bất kỳ None/NaN nào còn sót lại
            result_df = result_df.fillna({
                'timestamp': pd.NaT,  # Nếu dùng TimestampType
                'license_plate': '',
                'location': '',
                'status': '',
                'action': '',
                'event_type': '',
                'timestamp_unix': 0,
                'parked_duration_minutes': 0.0,
                'parked_blocks': 0,
                'total_cost': 0
            })
            
            # Đảm bảo DataFrame có đúng schema và không có None/NaN
            yield result_df  # SỬA: yield thay vì return
        
        # Nếu không có output, không yield gì cả
    
    def handleExpiredTimer(self, key, timerValues, expiredTimerInfo) -> Iterator[pd.DataFrame]:  # SỬA -> Iterator
        """
        Xử lý khi timer hết hạn - cập nhật định kỳ cho xe đang đỗ
        """
        if not self.vehicle_state.exists():
            return  # Không yield
        
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
            return  # Không yield
        
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
            'timestamp': current_time,  # SỬA: datetime object
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
        
        # Tạo DataFrame với đúng schema và dtypes
        df = pd.DataFrame([output_row])
        required_columns = ['timestamp', 'timestamp_unix', 'license_plate', 'location', 
                          'status', 'action', 'parked_duration_minutes', 'parked_blocks', 
                          'total_cost', 'event_type']
        
        # Đảm bảo tất cả các cột có mặt
        for col in required_columns:
            if col not in df.columns:
                if col in ['timestamp', 'license_plate', 'location', 'status', 'action', 'event_type']:
                    df[col] = ''
                elif col == 'timestamp_unix':
                    df[col] = 0
                elif col == 'parked_duration_minutes':
                    df[col] = 0.0
                elif col in ['parked_blocks', 'total_cost']:
                    df[col] = 0
        
        # Convert và đảm bảo dtypes đúng - xử lý giống như handleInputRows
        # String columns: convert tất cả giá trị sang string, XÓA astype('object')
        string_cols = ['license_plate', 'location', 'status', 'action', 'event_type']
        for col in string_cols:
            if col in df.columns:
                # Convert tất cả giá trị sang string (bao gồm None -> 'None')
                df[col] = df[col].astype(str)
                # Thay thế 'None' và 'nan' bằng empty string
                df[col] = df[col].replace(['None', 'nan', 'NaN'], '')
                # XÓA dòng astype('object') - giữ 'string' tự nhiên
        
        # Timestamp column: đảm bảo là datetime
        if 'timestamp' in df.columns:
            # Nếu timestamp là datetime object, đảm bảo dtype là datetime64[ns]
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            # Đảm bảo dtype là datetime64[ns]
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Numeric columns: convert sang đúng dtype với xử lý lỗi
        df['timestamp_unix'] = pd.to_numeric(df['timestamp_unix'], errors='coerce').fillna(0).astype('int64')
        df['parked_duration_minutes'] = pd.to_numeric(df['parked_duration_minutes'], errors='coerce').fillna(0.0).astype('float64')
        df['parked_blocks'] = pd.to_numeric(df['parked_blocks'], errors='coerce').fillna(0).astype('int64')
        df['total_cost'] = pd.to_numeric(df['total_cost'], errors='coerce').fillna(0).astype('int64')
        
        # Đảm bảo thứ tự cột đúng
        result_df = df[required_columns].copy()
        
        # Reset index để đảm bảo DataFrame có index hợp lệ
        result_df = result_df.reset_index(drop=True)
        
        # Kiểm tra và đảm bảo không có None/NaN trong DataFrame
        result_df = result_df.fillna({
            'timestamp': pd.NaT,  # Nếu dùng TimestampType
            'license_plate': '',
            'location': '',
            'status': '',
            'action': '',
            'event_type': '',
            'timestamp_unix': 0,
            'parked_duration_minutes': 0.0,
            'parked_blocks': 0,
            'total_cost': 0
        })
        
        yield result_df  # SỬA: yield
    
    def close(self) -> None:
        """Cleanup khi đóng processor"""
        pass

def create_spark_session(checkpoint_location=None):
    """Tạo SparkSession với cấu hình phù hợp"""
    builder = SparkSession.builder \
        .appName("ParkingStatefulProcessor") \
        .config("spark.sql.streaming.stateStore.maintenanceInterval", "60s") \
        .config("spark.sql.streaming.stateStore.providerClass", "org.apache.spark.sql.execution.streaming.state.RocksDBStateStoreProvider") \
        .config("spark.hadoop.fs.defaultFS", "file:///") \
        .config("spark.sql.streaming.fileSource.schema.forceNullable", "true")
    
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
    # Dùng "earliest" để đọc từ đầu topic (bao gồm dữ liệu cũ)
    # Nếu muốn chỉ đọc dữ liệu mới, đổi thành "latest"
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", args.kafka_bootstrap) \
        .option("subscribe", args.input_topic) \
        .option("startingOffsets", "earliest") \
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
    
    # Convert timestamp_unix từ BIGINT sang TIMESTAMP cho watermark
    df_with_timestamp = df_parsed.withColumn(
        "event_time", 
        col("timestamp_unix").cast("timestamp")
    )
    
    # Áp dụng watermark
    df_with_watermark = df_with_timestamp.withWatermark("event_time", "10 minutes")
    
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
    # DataFrame rỗng từ create_empty_dataframe() sẽ không có rows, Spark sẽ tự động skip
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

