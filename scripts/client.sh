#!/bin/bash
if [ $# -lt 2 ]; then
    echo "Usage: $0 <your_name> <peer_name> [server_url]"
    exit 1
fi

YOUR_NAME=$1
PEER_NAME=$2
SERVER_URL=$3

echo "Starting chat client for $YOUR_NAME (talking to $PEER_NAME)..."
cd client
PYTHONPATH=.. python client.py "$YOUR_NAME" "$PEER_NAME" "$SERVER_URL"