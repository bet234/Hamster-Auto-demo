#!/bin/bash

# Ensure that Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3."
    exit 1
fi

# Ensure that the requests module is installed
if ! python3 -c "import requests" &> /dev/null; then
    echo "The requests module is not installed. Installing it..."
    pip install requests
fi

# Run the Python script
python3 -c "
$(curl -fsSL https://raw.githubusercontent.com/bet234/Hamster-Auto-demo/main/hamster2.py)
"
