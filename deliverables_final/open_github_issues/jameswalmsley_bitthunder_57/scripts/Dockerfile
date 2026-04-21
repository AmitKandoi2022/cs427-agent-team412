FROM ubuntu:22.04

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc-arm-none-eabi \
    libnewlib-arm-none-eabi \
    git \
    python3 \
    make \
    qemu-system-arm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app