#!/bin/bash
# Start script for Render deployment
echo "Starting Bug Tester AI application..."

# Get port from environment variable
PORT=${PORT:-5000}

# Start the application with Gunicorn
echo "Starting Gunicorn on port $PORT..."
gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 api_server:app
