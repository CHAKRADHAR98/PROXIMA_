#!/bin/bash
# Activate virtual environment (if you created one)
if [ -d "crowd_env" ]; then
  source crowd_env/bin/activate
fi

# Run the main script
python main.py

# Run analysis scripts
read -p "Do you want to process the results? (y/n) " choice
if [ "$choice" = "y" ]; then
  echo "Processing results..."
  python abnormal_data_process.py
  python crowd_data_present.py
  python movement_data_present.py
fi