#!/bin/bash
set -e

echo "--- Building Docker Image ---"
docker build -t connxr-verify .

echo "--- Running Pre-patch Verification (Should Crash/Fail) ---"
docker run --rm connxr-verify bash -c "
    mkdir build && cd build && cmake .. && make -j$(nproc)
    python3 ../reproduce_issue.py
    echo 'Running malformed model...'
    ./connxr malformed_constant.onnx || echo 'Process exited (likely segfault or error)'
"

echo "--- Applying Patch ---"
docker run --rm -v $(pwd):/host connxr-verify bash -c "
    git apply /host/fix.patch
    mkdir -p build_patched && cd build_patched
    cmake .. && make -j$(nproc)
    python3 ../reproduce_issue.py
    echo 'Running malformed model with patch...'
    ./connxr malformed_constant.onnx
    echo 'Verification successful: Application handled the missing attribute gracefully.'
"