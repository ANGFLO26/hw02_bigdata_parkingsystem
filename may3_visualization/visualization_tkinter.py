#!/usr/bin/env python3
"""
Ứng dụng Visualization Bãi Đỗ Xe sử dụng Tkinter
Đọc dữ liệu từ Kafka topic parking-processed-results và hiển thị real-time
"""

import json
import threading
import time
import re
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from collections import defaultdict

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tất cả vị trí (6 tầng, mỗi tầng 10 chỗ)
ALL_LOCATIONS = []
for floor in ['A', 'B', 'C', 'D', 'E', 'F']:
    for num in range(1, 11):
        ALL_LOCATIONS.append(f"{floor}{num}")

class ParkingVisualizationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚗 Bãi Đỗ Xe - Dashboard Real-time")
        self.root.geometry("1400x900")
        
        # State variables
        self.parking_lot_map = {}  # {location: vehicle_info}
        self.vehicle_details = {}  # {license_plate: details}
        self.statistics = {
            'total_locations': 60,
            'occupied_count': 0,
            'available_count': 60,
            'total_revenue': 0
        }
        
        # Kafka connection
        self.consumer = None
        self.consumer_thread = None
        self.running = False
        self.connection_status = "Chưa kết nối"
        
        # Default config
        self.kafka_bootstrap = "10.38.11.118:9092"
        self.kafka_topic = "parking-processed-results"
        
        # Create UI
        self.create_ui()
        
        # Start auto-refresh
        self.update_display()
        
    def create_ui(self):
        """Tạo giao diện"""
        # Top frame - Configuration
        config_frame = ttk.Frame(self.root, padding="10")
        config_frame.pack(fill=tk.X)
        
        ttk.Label(config_frame, text="Kafka Bootstrap Servers:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.kafka_bootstrap_var = tk.StringVar(value=self.kafka_bootstrap)
        ttk.Entry(config_frame, textvariable=self.kafka_bootstrap_var, width=30).grid(row=0, column=1, padx=5)
        
        ttk.Label(config_frame, text="Kafka Topic:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.kafka_topic_var = tk.StringVar(value=self.kafka_topic)
        ttk.Entry(config_frame, textvariable=self.kafka_topic_var, width=25).grid(row=0, column=3, padx=5)
        
        ttk.Button(config_frame, text="🔄 Kết nối/Khởi động lại", command=self.start_connection).grid(row=0, column=4, padx=5)
        ttk.Button(config_frame, text="⏹️ Dừng", command=self.stop_connection).grid(row=0, column=5, padx=5)
        
        self.status_label = ttk.Label(config_frame, text="Trạng thái: " + self.connection_status, foreground="red")
        self.status_label.grid(row=0, column=6, padx=10)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(self.root, text="📊 Thống Kê", padding="10")
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.total_locations_label = ttk.Label(stats_frame, text="Tổng số chỗ: 60", font=("Arial", 12, "bold"))
        self.total_locations_label.grid(row=0, column=0, padx=20)
        
        self.occupied_label = ttk.Label(stats_frame, text="Đã đỗ: 0", font=("Arial", 12, "bold"), foreground="red")
        self.occupied_label.grid(row=0, column=1, padx=20)
        
        self.available_label = ttk.Label(stats_frame, text="Trống: 60", font=("Arial", 12, "bold"), foreground="green")
        self.available_label.grid(row=0, column=2, padx=20)
        
        self.revenue_label = ttk.Label(stats_frame, text="Doanh thu: 0 VNĐ", font=("Arial", 12, "bold"), foreground="blue")
        self.revenue_label.grid(row=0, column=3, padx=20)
        
        # Main content frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left: Parking map
        map_frame = ttk.LabelFrame(main_frame, text="🗺️ Bản Đồ Bãi Xe", padding="10")
        map_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create scrollable canvas for parking map
        canvas_frame = ttk.Frame(map_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.map_canvas = tk.Canvas(canvas_frame, bg="white")
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.map_canvas.yview)
        self.map_scrollable_frame = ttk.Frame(self.map_canvas)
        
        self.map_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.map_canvas.configure(scrollregion=self.map_canvas.bbox("all"))
        )
        
        self.map_canvas.create_window((0, 0), window=self.map_scrollable_frame, anchor="nw")
        self.map_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.map_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Right: Vehicle details table
        details_frame = ttk.LabelFrame(main_frame, text="📋 Chi Tiết Xe Đang Đỗ", padding="10")
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)
        
        # Create treeview for vehicle details
        columns = ('Vị trí', 'Biển số', 'Thời gian đỗ (phút)', 'Số block', 'Tiền (VNĐ)')
        self.details_tree = ttk.Treeview(details_frame, columns=columns, show='headings', height=25)
        
        for col in columns:
            self.details_tree.heading(col, text=col)
            self.details_tree.column(col, width=120, anchor=tk.CENTER)
        
        self.details_tree.pack(fill=tk.BOTH, expand=True)
        
        # Log frame at bottom
        log_frame = ttk.LabelFrame(self.root, text="📝 Log", padding="5")
        log_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=5, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def log(self, message):
        """Ghi log vào text widget"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def parse_license_plate(self, license_plate_str):
        """Parse license plate từ format ('30B-55555',) thành 30B-55555"""
        if not license_plate_str:
            return ""
        # Remove tuple format
        match = re.search(r"['\"]([^'\"]+)['\"]", str(license_plate_str))
        if match:
            return match.group(1)
        return str(license_plate_str).strip("()',\"")
        
    def connect_kafka(self):
        """Kết nối đến Kafka"""
        try:
            bootstrap_servers = self.kafka_bootstrap_var.get()
            topic = self.kafka_topic_var.get()
            
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=[bootstrap_servers],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=1000,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='parking-visualization-tkinter'
            )
            
            logger.info(f"Đã kết nối đến Kafka: {bootstrap_servers}")
            self.connection_status = "✅ Đã kết nối"
            self.status_label.config(text=f"Trạng thái: {self.connection_status}", foreground="green")
            self.log(f"Đã kết nối đến Kafka: {bootstrap_servers}, Topic: {topic}")
            return consumer
        except Exception as e:
            logger.error(f"Lỗi kết nối Kafka: {e}")
            self.connection_status = "❌ Lỗi kết nối"
            self.status_label.config(text=f"Trạng thái: {self.connection_status}", foreground="red")
            self.log(f"Lỗi kết nối Kafka: {e}")
            return None
    
    def process_message(self, data):
        """Xử lý message từ Kafka"""
        try:
            event_type = data.get('event_type', 'vehicle_event')
            action = data.get('action', '')
            license_plate_raw = data.get('license_plate', '')
            license_plate = self.parse_license_plate(license_plate_raw)
            location = data.get('location', '')
            
            # Validate dữ liệu
            if not license_plate or not location:
                logger.warning(f"Message thiếu dữ liệu: {data}")
                return
            
            if event_type in ['vehicle_event', 'timer_event']:
                if action == 'vehicle_entered':
                    # Xe mới vào
                    self.parking_lot_map[location] = {
                        'license_plate': license_plate,
                        'status': 'ENTERING',
                        'parked_duration_minutes': 0,
                        'parked_blocks': 0,
                        'total_cost': 0
                    }
                    self.vehicle_details[license_plate] = {
                        'location': location,
                        'status': 'ENTERING'
                    }
                    self.log(f"Xe {license_plate} vào tại {location}")
                
                elif action in ['vehicle_parked', 'parking_updated', 'periodic_update']:
                    # Xe đã đỗ hoặc cập nhật
                    parked_duration = data.get('parked_duration_minutes', 0)
                    parked_blocks = data.get('parked_blocks', 0)
                    total_cost = data.get('total_cost', 0)
                    
                    self.parking_lot_map[location] = {
                        'license_plate': license_plate,
                        'status': 'PARKED',
                        'parked_duration_minutes': parked_duration,
                        'parked_blocks': parked_blocks,
                        'total_cost': total_cost
                    }
                    self.vehicle_details[license_plate] = {
                        'location': location,
                        'status': 'PARKED',
                        'parked_duration_minutes': parked_duration,
                        'parked_blocks': parked_blocks,
                        'total_cost': total_cost
                    }
                    self.log(f"Cập nhật: {license_plate} tại {location} - {parked_duration:.1f} phút - {total_cost:,} VNĐ")
                
                elif action == 'vehicle_exiting':
                    # Xe đang ra
                    if location in self.parking_lot_map:
                        vehicle_info = self.parking_lot_map[location]
                        license_plate_exit = vehicle_info.get('license_plate', '')
                        del self.parking_lot_map[location]
                        if license_plate_exit in self.vehicle_details:
                            del self.vehicle_details[license_plate_exit]
                        self.log(f"Xe {license_plate_exit} ra khỏi {location}")
            
            # Cập nhật thống kê
            self.update_statistics()
            
        except Exception as e:
            logger.error(f"Lỗi xử lý message: {e}")
            self.log(f"Lỗi xử lý message: {e}")
    
    def update_statistics(self):
        """Cập nhật thống kê"""
        self.statistics['occupied_count'] = len(self.parking_lot_map)
        self.statistics['available_count'] = self.statistics['total_locations'] - self.statistics['occupied_count']
        self.statistics['total_revenue'] = sum(
            v.get('total_cost', 0) for v in self.parking_lot_map.values()
        )
    
    def kafka_consumer_loop(self):
        """Vòng lặp đọc messages từ Kafka"""
        while self.running:
            try:
                if self.consumer is None:
                    self.consumer = self.connect_kafka()
                    if self.consumer is None:
                        time.sleep(5)
                        continue
                
                # Poll messages
                messages = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, message_list in messages.items():
                    for message in message_list:
                        data = message.value if isinstance(message.value, dict) else json.loads(message.value)
                        self.process_message(data)
                
            except Exception as e:
                error_msg = str(e)
                if "wakeup" in error_msg.lower():
                    logger.debug(f"Consumer đang đóng: {e}")
                    break
                elif isinstance(e, KafkaError):
                    logger.error(f"Lỗi Kafka: {e}")
                    self.connection_status = "❌ Lỗi kết nối"
                    self.status_label.config(text=f"Trạng thái: {self.connection_status}", foreground="red")
                    try:
                        if self.consumer:
                            self.consumer.close()
                    except:
                        pass
                    self.consumer = None
                    time.sleep(5)
                else:
                    logger.error(f"Lỗi không mong đợi: {e}")
                    self.log(f"Lỗi: {e}")
                    time.sleep(1)
        
        # Cleanup
        try:
            if self.consumer:
                self.consumer.close()
        except Exception as e:
            logger.debug(f"Lỗi khi đóng consumer: {e}")
        finally:
            self.consumer = None
    
    def start_connection(self):
        """Bắt đầu kết nối Kafka"""
        self.stop_connection()
        
        self.kafka_bootstrap = self.kafka_bootstrap_var.get()
        self.kafka_topic = self.kafka_topic_var.get()
        
        self.running = True
        self.consumer = self.connect_kafka()
        
        if self.consumer:
            self.consumer_thread = threading.Thread(
                target=self.kafka_consumer_loop,
                daemon=True
            )
            self.consumer_thread.start()
            self.log("Đã khởi động consumer thread")
        else:
            self.running = False
            messagebox.showerror("Lỗi", "Không thể kết nối đến Kafka!")
    
    def stop_connection(self):
        """Dừng kết nối Kafka"""
        self.running = False
        
        if self.consumer:
            try:
                self.consumer.wakeup()
            except:
                pass
            try:
                self.consumer.close()
            except:
                pass
            self.consumer = None
        
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=2)
        self.consumer_thread = None
        
        self.connection_status = "Đã dừng"
        self.status_label.config(text=f"Trạng thái: {self.connection_status}", foreground="orange")
        self.log("Đã dừng kết nối Kafka")
    
    def create_parking_map(self):
        """Tạo bản đồ bãi đỗ xe"""
        # Clear existing widgets
        for widget in self.map_scrollable_frame.winfo_children():
            widget.destroy()
        
        floors = ['A', 'B', 'C', 'D', 'E', 'F']
        
        for floor_idx, floor in enumerate(floors):
            # Floor label
            floor_label = ttk.Label(self.map_scrollable_frame, text=f"Tầng {floor}", font=("Arial", 14, "bold"))
            floor_label.grid(row=floor_idx * 2, column=0, columnspan=10, pady=10, sticky=tk.W)
            
            # Create 10 parking spots for this floor
            for i in range(10):
                location = f"{floor}{i+1}"
                spot_frame = ttk.Frame(self.map_scrollable_frame, relief=tk.RAISED, borderwidth=2)
                spot_frame.grid(row=floor_idx * 2 + 1, column=i, padx=2, pady=2, sticky="nsew")
                
                if location in self.parking_lot_map:
                    # Occupied spot
                    vehicle_info = self.parking_lot_map[location]
                    license_plate = vehicle_info.get('license_plate', 'N/A')
                    parked_duration = vehicle_info.get('parked_duration_minutes', 0)
                    total_cost = vehicle_info.get('total_cost', 0)
                    
                    spot_frame.config(style="Occupied.TFrame")
                    ttk.Label(spot_frame, text=location, font=("Arial", 9, "bold"), 
                             background="#ff6b6b", foreground="white").pack(fill=tk.X)
                    ttk.Label(spot_frame, text=license_plate[:10], font=("Arial", 8), 
                             background="#ff6b6b", foreground="white").pack()
                    ttk.Label(spot_frame, text=f"{parked_duration:.1f} phút", font=("Arial", 7), 
                             background="#ff6b6b", foreground="white").pack()
                    ttk.Label(spot_frame, text=f"{total_cost:,} đ", font=("Arial", 7, "bold"), 
                             background="#ff6b6b", foreground="white").pack()
                else:
                    # Available spot
                    spot_frame.config(style="Available.TFrame")
                    ttk.Label(spot_frame, text=location, font=("Arial", 9, "bold"), 
                             background="#51cf66", foreground="white").pack(fill=tk.X)
                    ttk.Label(spot_frame, text="TRỐNG", font=("Arial", 10, "bold"), 
                             background="#51cf66", foreground="white").pack(expand=True)
        
        # Configure styles
        style = ttk.Style()
        style.configure("Occupied.TFrame", background="#ff6b6b")
        style.configure("Available.TFrame", background="#51cf66")
    
    def update_details_table(self):
        """Cập nhật bảng chi tiết xe"""
        # Clear existing items
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)
        
        # Add current vehicles
        for location, vehicle_info in sorted(self.parking_lot_map.items()):
            license_plate = vehicle_info.get('license_plate', 'N/A')
            parked_duration = vehicle_info.get('parked_duration_minutes', 0)
            parked_blocks = vehicle_info.get('parked_blocks', 0)
            total_cost = vehicle_info.get('total_cost', 0)
            
            self.details_tree.insert('', tk.END, values=(
                location,
                license_plate,
                f"{parked_duration:.1f}",
                parked_blocks,
                f"{total_cost:,}"
            ))
    
    def update_display(self):
        """Cập nhật hiển thị"""
        # Update statistics
        self.total_locations_label.config(text=f"Tổng số chỗ: {self.statistics['total_locations']}")
        self.occupied_label.config(text=f"Đã đỗ: {self.statistics['occupied_count']}")
        self.available_label.config(text=f"Trống: {self.statistics['available_count']}")
        self.revenue_label.config(text=f"Doanh thu: {self.statistics['total_revenue']:,} VNĐ")
        
        # Update parking map
        self.create_parking_map()
        
        # Update details table
        self.update_details_table()
        
        # Schedule next update
        self.root.after(2000, self.update_display)  # Update every 2 seconds

def main():
    root = tk.Tk()
    app = ParkingVisualizationApp(root)
    
    def on_closing():
        app.stop_connection()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()

