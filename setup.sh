#!/bin/bash
echo "Setting up Crowd-Analysis with YOLOv8..."

# Create directories
mkdir -p processed_data
mkdir -p model_data

# Download DeepSORT model if needed
if [ ! -f "model_data/mars-small128.pb" ]; then
  echo "Downloading DeepSORT model..."
  wget -P model_data https://github.com/nwojke/deep_sort/raw/master/resources/networks/mars-small128.pb
fi

# Test YOLO model download - this will download the model on first use
python -c "from ultralytics import YOLO; model = YOLO('yolov8n.pt'); print('YOLOv8 nano model successfully loaded')"

echo "Setup complete!"