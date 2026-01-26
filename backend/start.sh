#!/bin/bash
# Start the backend with GStreamer library paths configured for macOS

# Set up GStreamer/GLib library paths
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:/opt/homebrew/opt/gstreamer/lib:$DYLD_LIBRARY_PATH"
export GI_TYPELIB_PATH="/opt/homebrew/lib/girepository-1.0:$GI_TYPELIB_PATH"
export GST_PLUGIN_PATH="/opt/homebrew/lib/gstreamer-1.0"

# Change to the backend directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start the FastAPI server
echo "Starting backend with GStreamer support..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
