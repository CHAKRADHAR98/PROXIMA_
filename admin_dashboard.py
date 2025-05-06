import sys
import os
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                            QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QTableWidget, QTableWidgetItem, QComboBox, QSlider,
                            QFileDialog, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QDateTime
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor
import pyqtgraph as pg
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# For video display
import cv2
import numpy as np
from PIL import Image

# Import our existing analysis modules
from tracking import detect_human
from yolov8_detector import YOLOv8Detector
from deep_sort import nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker
from deep_sort import generate_detections as gdet
from util import kinetic_energy

class AdminDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Dashboard title and size
        self.setWindowTitle("Crowd Analysis Admin Dashboard")
        self.setGeometry(100, 100, 1280, 720)
        
        # Initialize the UI
        self.init_UI()
        
        # Initialize database
        self.init_database()
        
        # Start with video processing stopped
        self.is_processing = False
        self.is_recording = False
        
        # Status update timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
