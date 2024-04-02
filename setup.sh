#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python could not be found. Please install Python 3."
    exit
fi

# Install necessary Python packages
python3 -m pip install --upgrade pip
python3 -m pip install flask flask_sqlalchemy transformers diffusers torch pillow

# Check for LUCRA_AI_QUERIES_DATABASE_URI environment variable
if [ -z "${LUCRA_AI_QUERIES_DATABASE_URI}" ]; then
    echo "LUCRA_AI_QUERIES_DATABASE_URI environment variable is not set. Please set it."
    exit
fi

# Start the Python application
python3 main.py