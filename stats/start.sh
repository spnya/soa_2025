#!/bin/bash

echo "Starting Statistics Service..."

# Generate gRPC files
echo "Generating gRPC files..."
python -m grpc_tools.protoc \
    --proto_path=. \
    --python_out=. \
    --grpc_python_out=. \
    statistics.proto

# Check if files were generated
if [ -f "statistics_pb2.py" ] && [ -f "statistics_pb2_grpc.py" ]; then
    echo "✓ gRPC files generated successfully"
else
    echo "✗ Failed to generate gRPC files"
    exit 1
fi

# Start consumer in background
echo "Starting Kafka consumer..."
python consumer.py &
CONSUMER_PID=$!
echo "✓ Consumer started with PID: $CONSUMER_PID"

# Wait a bit for consumer to initialize
sleep 5

# Start gRPC server in background  
echo "Starting gRPC server..."
python statistics_server.py &
GRPC_PID=$!
echo "✓ gRPC server started with PID: $GRPC_PID"

# Function to handle shutdown
cleanup() {
    echo "Shutting down services..."
    kill $CONSUMER_PID 2>/dev/null
    kill $GRPC_PID 2>/dev/null
    exit 0
}

# Set trap for cleanup
trap cleanup SIGTERM SIGINT

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?