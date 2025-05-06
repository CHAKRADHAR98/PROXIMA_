#!/usr/bin/env python3

# This script checks for common errors in the admin_dashboard.py file
import re

# Read the file
with open('admin_dashboard.py', 'r') as f:
    content = f.read()

# Check for method name inconsistencies
if 'def init_ui' in content and 'self.init_UI()' in content:
    print("Method name inconsistency found: init_ui vs init_UI")
    content = content.replace('def init_ui', 'def init_UI')
    print("Fixed: Renamed method to init_UI")

# Check for datetime usage
if 'datetime.datetime.now()' in content:
    print("Incorrect datetime usage found: datetime.datetime.now()")
    content = content.replace('datetime.datetime.now()', 'datetime.now()')
    print("Fixed: Changed to datetime.now()")

# Write the fixed content back
with open('admin_dashboard.py', 'w') as f:
    f.write(content)

print("Check and fix completed for admin_dashboard.py")