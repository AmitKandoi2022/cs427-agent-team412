#!/bin/bash
set -e

# 1. Setup workspace
REPO_URL="https://github.com/zhewang2001/Project.git"
# Ensure clean start if directory exists
rm -rf verification_repo
git clone $REPO_URL verification_repo
cd verification_repo

# 2. Apply the patch
if [ -f "../../fix.patch" ]; then
    echo "Applying patch..."
    git apply ../../fix.patch
else
    echo "Warning: fix.patch not found at ../../fix.patch"
fi

# 3. Create a Dockerfile for Android build
# Updated to use JDK 11 and Temurin distribution to match checkstyle.yml
cat << 'EOF' > Dockerfile
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

# Ensure gradlew is executable (matching the workflow step)
RUN chmod +x gradlew

# Run Checkstyle exactly as defined in the workflow
# Using checkstyleMain and checkstyleTest
CMD ["./gradlew", "checkstyleDebug"]
EOF

# 4. Build and Run
echo "Building Docker environment..."
docker build -t android-checkstyle-verify .

echo "Running Checkstyle..."
# Create a local directory for reports to mimic the "Upload Artifact" step
# mkdir -p ./checkstyle-reports

# Run docker and mount the reports directory to extract the results
docker run --rm \
    -v "/Users/zhangyi.lu/Projects/checkstyle-reports:/project/app/build/reports/checkstyle/" \
    android-checkstyle-verify

echo "Verification complete. Reports are available in ./checkstyle-reports"