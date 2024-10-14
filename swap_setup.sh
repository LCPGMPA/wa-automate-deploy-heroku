#!/bin/bash

# Create a 1 GB swap file if it doesn't already exist
if [ ! -f /swapfile ]; then
    echo "Creating swap file..."
    fallocate -l 1G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
fi

# Try to activate the swap file
echo "Activating swap file..."
swapon /swapfile || echo "Warning: Unable to activate swap."

# Display swap status (for debugging)
free -h
