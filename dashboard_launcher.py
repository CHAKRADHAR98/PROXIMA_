#!/usr/bin/env python3

import os
import sys
from PyQt5.QtCore import QLibraryInfo

# Fix Qt plugin path issue
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(QLibraryInfo.PluginsPath)

# Make sure required directories exist
os.makedirs("processed_data", exist_ok=True)
os.makedirs("model_data", exist_ok=True)
os.makedirs("recordings", exist_ok=True)

# Import after environment variables are set
from PyQt5.QtWidgets import QApplication
from admin_dashboard import AdminDashboard

if __name__ == "__main__":
    # Start the dashboard application
    app = QApplication(sys.argv)
    window = AdminDashboard()
    window.show()
    sys.exit(app.exec_())