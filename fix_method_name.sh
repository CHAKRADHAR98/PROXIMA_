#!/bin/bash

# Fix method name discrepancy in admin_dashboard.py
sed -i 's/def init_ui/def init_UI/g' admin_dashboard.py
sed -i 's/self.init_ui()/self.init_UI()/g' admin_dashboard.py

echo "Fixed method name in admin_dashboard.py"