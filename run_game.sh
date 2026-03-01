#!/bin/bash

# Check if python3 or python is installed
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python is not installed. Please install Python 3.8+."
    exit 1
fi

# Check for rich library
$PYTHON_CMD -c "import rich" &>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required 'rich' library..."
    $PYTHON_CMD -m pip install rich
fi

# Run the game
$PYTHON_CMD main.py
