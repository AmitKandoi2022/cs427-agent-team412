#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="swarmkit-fix-test"

echo "==> Building Docker image..."
docker build -t ${IMAGE_NAME} .

echo "==> Running test suite..."
set +e
OUTPUT=$(docker run --rm ${IMAGE_NAME} 2>&1)
EXIT_CODE=$?
set -e

echo "$OUTPUT"

echo "==> Analyzing results..."

if [ $EXIT_CODE -ne 0 ]; then
    echo "Tests failed"
    if echo "$OUTPUT" | grep -i "goroutine leak"; then
        echo "Goroutine leak issue still present"
    fi
    exit 1
fi

if echo "$OUTPUT" | grep -i "goroutine leak"; then
    echo "Leak warning detected despite passing tests"
    exit 1
fi

echo "All tests passed and no goroutine leaks detected"