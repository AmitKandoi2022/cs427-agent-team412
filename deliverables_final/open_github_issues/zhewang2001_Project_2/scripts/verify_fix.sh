#!/bin/bash
set -e

# 1. Setup workspace
REPO_URL="https://github.com/zhewang2001/Project.git"
git clone $REPO_URL verification_repo
cd verification_repo

# 2. Apply the patch
echo "Applying patch..."
git apply ../../fix.patch

# 3. Create a Dockerfile for Android build
# We use a pre-configured Android SDK image to save time
cat << 'EOF' > Dockerfile
# Use the official Eclipse Temurin image for JDK 17
FROM eclipse-temurin:17-jdk-jammy

# Set environment variables for Android SDK
ENV ANDROID_SDK_ROOT /opt/android-sdk
ENV PATH ${PATH}:${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/platform-tools

# Install dependencies
RUN apt-get update && apt-get install -y wget unzip git

# Download and install Android Command Line Tools
RUN mkdir -p ${ANDROID_SDK_ROOT}/cmdline-tools && \
    wget https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip -O /tmp/tools.zip && \
    unzip /tmp/tools.zip -d ${ANDROID_SDK_ROOT}/cmdline-tools && \
    mv ${ANDROID_SDK_ROOT}/cmdline-tools/cmdline-tools ${ANDROID_SDK_ROOT}/cmdline-tools/latest && \
    rm /tmp/tools.zip

# Accept licenses
RUN yes | sdkmanager --licenses

WORKDIR /project
COPY . .

# Ensure gradlew is executable
RUN chmod +x gradlew

# Run Checkstyle
CMD ["./gradlew", ":app:checkstyle"]
EOF

# 4. Build and Run
echo "Building Docker environment..."
docker build -t android-checkstyle-verify .

echo "Running Checkstyle..."
docker run --rm android-checkstyle-verify