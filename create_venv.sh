#!/bin/bash
echo "Creating Python virtual environment for Crowd-Analysis..."

# Create virtual environment
python -m venv crowd_env

# Activate the environment (this will be different on Windows)
source crowd_env/bin/activate

# Install dependencies
pip install -r requirements.txt

echo "Virtual environment created and dependencies installed!"
echo "To activate the environment, run: source crowd_env/bin/activate"