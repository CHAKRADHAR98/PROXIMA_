#!/bin/bash

# Fix the datetime.datetime.now() error in admin_dashboard.py
sed -i 's/self.fps_time = datetime.datetime.now()/self.fps_time = datetime.now()/g' admin_dashboard.py
sed -i 's/current_time = datetime.datetime.now()/current_time = datetime.now()/g' admin_dashboard.py
sed -i 's/self.recording_start_time = datetime.datetime.now()/self.recording_start_time = datetime.now()/g' admin_dashboard.py
sed -i 's/elapsed = (datetime.datetime.now() - self.recording_start_time)/elapsed = (datetime.now() - self.recording_start_time)/g' admin_dashboard.py

echo "Fixed datetime references in admin_dashboard.py"