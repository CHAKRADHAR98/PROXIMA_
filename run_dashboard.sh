#!/bin/bash

# Export the Qt platform plugin path directly
export QT_QPA_PLATFORM_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/qt5/plugins
echo "Set QT_QPA_PLATFORM_PLUGIN_PATH to $QT_QPA_PLATFORM_PLUGIN_PATH"

# Activate virtual environment if it exists
if [ -d "crowd_env" ]; then
  source crowd_env/bin/activate
fi

# Run the dashboard
python -c "
import os
import sys
from PyQt5.QtWidgets import QApplication
from admin_dashboard import AdminDashboard

# Ensure directories exist
os.makedirs('processed_data', exist_ok=True)
os.makedirs('model_data', exist_ok=True)
os.makedirs('recordings', exist_ok=True)

# Start dashboard
app = QApplication(sys.argv)
window = AdminDashboard()
window.show()
sys.exit(app.exec_())
"