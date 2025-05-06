#!/usr/bin/env python3

import os
import sys
from PyQt5.QtCore import QLibraryInfo

# Fix Qt plugin path issue
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(QLibraryInfo.PluginsPath)

# For OpenCV Qt conflict
cv2_qt_path = None
try:
    import cv2
    import os
    cv2_qt_path = os.path.join(os.path.dirname(cv2.__file__), "qt/plugins")
    if os.path.exists(cv2_qt_path):
        os.rename(cv2_qt_path, f"{cv2_qt_path}_disabled")
        print(f"Temporarily disabled OpenCV Qt plugins at: {cv2_qt_path}")
except:
    pass

try:
    # Make sure required directories exist
    os.makedirs("processed_data", exist_ok=True)
    os.makedirs("model_data", exist_ok=True)
    os.makedirs("recordings", exist_ok=True)

    # Import after environment variables are set
    from PyQt5.QtWidgets import QApplication
    from simple_admin_dashboard import SimpleDashboard

    # Start the dashboard application
    app = QApplication(sys.argv)
    window = SimpleDashboard()
    window.show()
    result = app.exec_()
    
    # Restore OpenCV Qt plugins
    if cv2_qt_path and os.path.exists(f"{cv2_qt_path}_disabled"):
        os.rename(f"{cv2_qt_path}_disabled", cv2_qt_path)
        print(f"Restored OpenCV Qt plugins at: {cv2_qt_path}")
        
    sys.exit(result)
    
except Exception as e:
    print(f"Error: {e}")
    
    # Restore OpenCV Qt plugins on error
    if cv2_qt_path and os.path.exists(f"{cv2_qt_path}_disabled"):
        os.rename(f"{cv2_qt_path}_disabled", cv2_qt_path)
        print(f"Restored OpenCV Qt plugins at: {cv2_qt_path}")