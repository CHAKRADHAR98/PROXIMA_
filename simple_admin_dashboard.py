import sys
import os
import datetime
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                            QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QTableWidget, QTableWidgetItem, QComboBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap, QColor

# For video display
import cv2
import numpy as np

# Import our existing analysis modules
from yolov8_detector import YOLOv8Detector
from deep_sort import nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker
from deep_sort import generate_detections as gdet

class VideoThread(QThread):
    frame_update = pyqtSignal(np.ndarray)
    stats_update = pyqtSignal(int, int, bool)  # crowd_count, violation_count, abnormal_activity
    
    def __init__(self, video_source):
        super().__init__()
        self.video_source = video_source
        self.running = False
        
        # Initialize detector
        self.detector = YOLOv8Detector()
        
        # Initialize tracker
        model_filename = 'model_data/mars-small128.pb'
        max_cosine_distance = 0.7
        nn_budget = None
        self.encoder = gdet.create_box_encoder(model_filename, batch_size=1)
        metric = nn_matching.NearestNeighborDistanceMetric("cosine", max_cosine_distance, nn_budget)
        self.tracker = Tracker(metric, max_age=30)
        
    def run(self):
        self.running = True
        cap = cv2.VideoCapture(self.video_source)
        
        if not cap.isOpened():
            print("Error: Could not open video source")
            return
            
        frame_count = 0
        
        while self.running:
            ret, frame = cap.read()
            
            if not ret:
                # End of video or error
                if isinstance(self.video_source, str):
                    # For file, restart
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    # For camera, error
                    print("Error: Video source disconnected")
                    break
            
            frame_count += 1
            
            # Process every other frame for performance
            if frame_count % 2 != 0:
                continue
                
            # Resize for performance
            frame = cv2.resize(frame, (640, 480))
            
            # Process frame
            processed_frame, stats = self.process_frame(frame, frame_count)
            
            # Convert BGR to RGB for Qt
            processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            
            # Emit signals
            self.frame_update.emit(processed_frame_rgb)
            self.stats_update.emit(*stats)
            
            # Control processing rate
            self.msleep(30)
            
        cap.release()
        
    def process_frame(self, frame, frame_count):
        # Detect humans
        boxes, confidences, centroids = self.detector.detect(frame)
        
        if len(boxes) > 0:
            # Prepare for tracking
            boxes_np = np.array(boxes)
            centroids_np = np.array(centroids)
            confidences_np = np.array(confidences)
            
            # Extract features
            features = np.array(self.encoder(frame, boxes_np))
            
            # Create detections
            detections = [Detection(bbox, score, centroid, feature) 
                        for bbox, score, centroid, feature in 
                        zip(boxes_np, confidences_np, centroids_np, features)]
            
            # Update tracker
            self.tracker.predict()
            expired = self.tracker.update(detections, frame_count)
            
            # Get confirmed tracks
            humans_detected = []
            for track in self.tracker.tracks:
                if not track.is_confirmed() or track.time_since_update > 5:
                    continue
                humans_detected.append(track)
            
            # Count violations
            violation_count = 0
            violate_set = set()
            
            # Draw boxes
            for i, track in enumerate(humans_detected):
                # Get bounding box
                [x, y, w, h] = list(map(int, track.to_tlbr().tolist()))
                
                # Get centroid
                [cx, cy] = list(map(int, track.positions[-1]))
                
                # Check social distance
                for j, track_2 in enumerate(humans_detected[i+1:], start=i+1):
                    [cx_2, cy_2] = list(map(int, track_2.positions[-1]))
                    distance = np.sqrt((cx - cx_2)**2 + (cy - cy_2)**2)
                    
                    if distance < 50:  # 50px threshold
                        violate_set.add(i)
                        violate_set.add(j)
                        
                # Draw bounding box
                if i in violate_set:
                    cv2.rectangle(frame, (x, y), (w, h), (0, 0, 255), 2)  # Red
                else:
                    cv2.rectangle(frame, (x, y), (w, h), (0, 255, 0), 2)  # Green
                    
                # Draw ID
                cv2.putText(frame, str(track.track_id), (x, y-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                            
            # Add stats to frame
            cv2.putText(frame, f"Count: {len(humans_detected)}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        
            cv2.putText(frame, f"Violations: {len(violate_set)}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        
            # Check for abnormal activity (simplified)
            abnormal = False
            if len(humans_detected) > 10 and len(violate_set) > 5:
                abnormal = True
                cv2.putText(frame, "ABNORMAL ACTIVITY", (frame.shape[1]//2 - 100, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                            
            return frame, (len(humans_detected), len(violate_set), abnormal)
            
        return frame, (0, 0, False)
        
    def stop(self):
        self.running = False


class SimpleDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.setWindowTitle("Crowd Analysis Dashboard")
        self.setGeometry(100, 100, 1024, 768)
        
        # Initialize UI
        self.setup_ui()
        
        # Setup database
        self.setup_database()
        
        # State
        self.is_processing = False
        self.video_source = None
        
    def setup_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create tab pages
        self.monitoring_tab = self.create_monitoring_tab()
        self.alerts_tab = self.create_alerts_tab()
        
        # Add tabs
        self.tabs.addTab(self.monitoring_tab, "Monitoring")
        self.tabs.addTab(self.alerts_tab, "Alerts")
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def create_monitoring_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Video display
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("No Video Feed")
        self.video_label.setStyleSheet("background-color: black; color: white;")
        layout.addWidget(self.video_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Video source
        self.video_source_combo = QComboBox()
        self.video_source_combo.addItem("Select Video Source")
        self.video_source_combo.addItem("Webcam")
        self.video_source_combo.addItem("Test Video")
        self.video_source_combo.currentIndexChanged.connect(self.handle_source_change)
        controls_layout.addWidget(self.video_source_combo)
        
        # Start/Stop button
        self.start_stop_button = QPushButton("Start Processing")
        self.start_stop_button.clicked.connect(self.toggle_processing)
        controls_layout.addWidget(self.start_stop_button)
        
        layout.addLayout(controls_layout)
        
        # Stats display
        stats_layout = QHBoxLayout()
        
        self.crowd_count_label = QLabel("Crowd Count: 0")
        self.violation_count_label = QLabel("Violations: 0")
        self.abnormal_label = QLabel("Status: Normal")
        
        stats_layout.addWidget(self.crowd_count_label)
        stats_layout.addWidget(self.violation_count_label)
        stats_layout.addWidget(self.abnormal_label)
        
        layout.addLayout(stats_layout)
        
        return tab
        
    def create_alerts_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Alerts table
        self.alert_table = QTableWidget()
        self.alert_table.setColumnCount(4)
        self.alert_table.setHorizontalHeaderLabels(["Time", "Type", "Severity", "Description"])
        self.alert_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.alert_table)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.clear_alerts_button = QPushButton("Clear Alerts")
        self.clear_alerts_button.clicked.connect(self.clear_alerts)
        controls_layout.addWidget(self.clear_alerts_button)
        
        self.test_alert_button = QPushButton("Test Alert")
        self.test_alert_button.clicked.connect(self.generate_test_alert)
        controls_layout.addWidget(self.test_alert_button)
        
        layout.addLayout(controls_layout)
        
        return tab
        
    def setup_database(self):
        # Initialize database
        self.conn = sqlite3.connect("dashboard.db")
        self.cursor = self.conn.cursor()
        
        # Create alerts table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            type TEXT,
            severity INTEGER,
            description TEXT
        )
        ''')
        self.conn.commit()
        
        # Load initial alerts
        self.update_alerts_table()
        
    def handle_source_change(self):
        source = self.video_source_combo.currentText()
        if source == "Webcam":
            self.video_source = 0
        elif source == "Test Video":
            self.video_source = "test.mp4"
        else:
            self.video_source = None
            
    def toggle_processing(self):
        if not self.is_processing:
            if self.video_source is None:
                self.statusBar().showMessage("Please select a video source")
                return
                
            # Start processing
            self.start_processing()
            self.is_processing = True
            self.start_stop_button.setText("Stop Processing")
        else:
            # Stop processing
            self.stop_processing()
            self.is_processing = False
            self.start_stop_button.setText("Start Processing")
            
    def start_processing(self):
        # Start video thread
        self.video_thread = VideoThread(self.video_source)
        self.video_thread.frame_update.connect(self.update_video_frame)
        self.video_thread.stats_update.connect(self.update_stats)
        self.video_thread.start()
        
        self.statusBar().showMessage("Processing started")
        
    def stop_processing(self):
        # Stop video thread
        if hasattr(self, 'video_thread') and self.video_thread.isRunning():
            self.video_thread.stop()
            self.video_thread.wait()
            
        self.statusBar().showMessage("Processing stopped")
        
    def update_video_frame(self, frame):
        # Update video display
        h, w, ch = frame.shape
        img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio))
        
    def update_stats(self, crowd_count, violation_count, abnormal_activity):
        # Update stats display
        self.crowd_count_label.setText(f"Crowd Count: {crowd_count}")
        self.violation_count_label.setText(f"Violations: {violation_count}")
        
        if abnormal_activity:
            self.abnormal_label.setText("Status: ABNORMAL")
            self.abnormal_label.setStyleSheet("color: red; font-weight: bold;")
            
            # Create alert
            self.add_alert("Abnormal Activity", 3, f"Detected abnormal crowd behavior: {crowd_count} people, {violation_count} violations")
        else:
            self.abnormal_label.setText("Status: Normal")
            self.abnormal_label.setStyleSheet("")
            
        # Check for violations
        if violation_count > 5 and not hasattr(self, 'last_violation_alert_time'):
            self.add_alert("Social Distance Violations", 2, f"Detected {violation_count} social distance violations")
            self.last_violation_alert_time = datetime.datetime.now()
            
        # Reset violation timer after 30 seconds
        if hasattr(self, 'last_violation_alert_time'):
            if (datetime.datetime.now() - self.last_violation_alert_time).total_seconds() > 30:
                delattr(self, 'last_violation_alert_time')
                
    def add_alert(self, alert_type, severity, description):
        # Add alert to database
        self.cursor.execute(
            "INSERT INTO alerts (type, severity, description) VALUES (?, ?, ?)",
            (alert_type, severity, description)
        )
        self.conn.commit()
        
        # Update alerts table
        self.update_alerts_table()
        
    def update_alerts_table(self):
        # Load alerts from database
        self.cursor.execute(
            "SELECT timestamp, type, severity, description FROM alerts ORDER BY timestamp DESC LIMIT 100"
        )
        alerts = self.cursor.fetchall()
        
        # Update table
        self.alert_table.setRowCount(len(alerts))
        
        for row, (timestamp, alert_type, severity, description) in enumerate(alerts):
            # Create items
            time_item = QTableWidgetItem(timestamp)
            type_item = QTableWidgetItem(alert_type)
            severity_item = QTableWidgetItem(str(severity))
            description_item = QTableWidgetItem(description)
            
            # Set color based on severity
            if severity >= 3:  # Critical
                color = QColor(255, 0, 0, 100)  # Red
            elif severity == 2:  # High
                color = QColor(255, 165, 0, 100)  # Orange
            else:  # Low
                color = QColor(255, 255, 0, 50)  # Yellow
                
            type_item.setBackground(color)
            
            # Add to table
            self.alert_table.setItem(row, 0, time_item)
            self.alert_table.setItem(row, 1, type_item)
            self.alert_table.setItem(row, 2, severity_item)
            self.alert_table.setItem(row, 3, description_item)
            
    def clear_alerts(self):
        # Clear alerts
        self.cursor.execute("DELETE FROM alerts")
        self.conn.commit()
        
        # Update table
        self.alert_table.setRowCount(0)
        self.statusBar().showMessage("Alerts cleared")
        
    def generate_test_alert(self):
        # Create test alert
        self.add_alert("Test Alert", 2, "This is a test alert")
        self.statusBar().showMessage("Test alert generated")
        
    def closeEvent(self, event):
        # Clean up on close
        if hasattr(self, 'video_thread') and self.video_thread.isRunning():
            self.video_thread.stop()
            self.video_thread.wait()
            
        if hasattr(self, 'conn'):
            self.conn.close()
            
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleDashboard()
    window.show()
    sys.exit(app.exec_())