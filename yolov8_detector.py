import torch
import numpy as np
from ultralytics import YOLO
from config import YOLO_CONFIG, MIN_CONF

class YOLOv8Detector:
    def __init__(self):
        # Configure CPU optimization
        torch.set_num_threads(4)  # Adjust based on your CPU cores
        
        # Load model
        self.model = YOLO(YOLO_CONFIG["MODEL_PATH"])
        self.model.to(YOLO_CONFIG["DEVICE"])
        
        # Optimize model
        self.model.fuse()
        self.conf_thresh = MIN_CONF
        
    def detect(self, frame):
        # Run inference
        results = self.model(frame, 
                           classes=0,  # Person class only 
                           conf=self.conf_thresh,
                           verbose=False)
        
        # Process detections
        boxes = []
        confidences = []
        centroids = []
        
        # Extract detection information
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                confidence = float(box.conf)
                
                # Calculate width and height
                w, h = x2 - x1, y2 - y1
                
                # Calculate centroid
                centroid = (int(x1 + w/2), int(y1 + h/2))
                
                # Add to lists
                boxes.append([x1, y1, w, h])
                confidences.append(confidence)
                centroids.append(centroid)
        
        return boxes, confidences, centroids