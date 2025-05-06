#!/bin/bash
echo "Setting up Crowd Analysis Admin Dashboard..."

# Ensure virtual environment is activated
if [ -d "crowd_env" ]; then
  source crowd_env/bin/activate
fi

# Install dashboard-specific requirements
pip install PyQt5>=5.15.0 pyqtgraph>=0.12.0

# Create required directories
mkdir -p recordings
mkdir -p processed_data
mkdir -p model_data

# Make sure the Deep SORT model exists
if [ ! -f "model_data/mars-small128.pb" ]; then
  echo "Downloading Deep SORT model..."
  wget -P model_data https://github.com/nwojke/deep_sort/raw/master/resources/networks/mars-small128.pb
fi

echo "Dashboard setup complete. Run with: python dashboard_launcher.py"