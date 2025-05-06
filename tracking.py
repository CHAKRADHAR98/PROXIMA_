import numpy as np
import cv2
from config import MIN_CONF, NMS_THRESH
from yolov8_detector import YOLOv8Detector

from deep_sort import nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker
from deep_sort import generate_detections as gdet

# Initialize YOLOv8 detector
detector = YOLOv8Detector()

def detect_human(net, ln, frame, encoder, tracker, time):
    # Run YOLOv8 detection
    boxes, confidences, centroids = detector.detect(frame)
    
    tracked_bboxes = []
    expired = []
    
    if len(boxes) > 0:
        # Convert to numpy arrays
        boxes = np.array(boxes)
        centroids = np.array(centroids)
        confidences = np.array(confidences)
        
        # Extract features for tracking
        features = np.array(encoder(frame, boxes))
        
        # Create detection objects
        detections = [Detection(bbox, score, centroid, feature) for bbox, score, centroid, feature in 
                    zip(boxes, confidences, centroids, features)]
        
        # Update tracker
        tracker.predict()
        expired = tracker.update(detections, time)
        
        # Get confirmed tracks
        for track in tracker.tracks:
            if not track.is_confirmed() or track.time_since_update > 5:
                continue
            tracked_bboxes.append(track)
    
    return [tracked_bboxes, expired]