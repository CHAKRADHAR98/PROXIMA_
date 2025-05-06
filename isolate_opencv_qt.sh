#!/bin/bash

# Move OpenCV's Qt plugins to prevent conflict
CV2_QT_PATH="$(python -c 'import os, cv2; print(os.path.join(os.path.dirname(cv2.__file__), "qt/plugins"))')"

if [ -d "$CV2_QT_PATH" ]; then
  echo "Found OpenCV Qt plugins at: $CV2_QT_PATH"
  echo "Temporarily renaming this directory to avoid conflicts"
  mv "$CV2_QT_PATH" "${CV2_QT_PATH}_disabled"
  
  # Now run the dashboard
  python dashboard_launcher.py
  
  # Restore the directory after dashboard exits
  mv "${CV2_QT_PATH}_disabled" "$CV2_QT_PATH"
else
  echo "OpenCV Qt plugins directory not found at: $CV2_QT_PATH"
  echo "Trying to run dashboard anyway..."
  python dashboard_launcher.py
fi