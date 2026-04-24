FROM python:3.11-slim

# Install git + bash
RUN apt-get update && apt-get install -y git bash && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy scripts into container
COPY verify_fix.py /workspace/verify_fix.py
COPY run_verify.sh /workspace/run_verify.sh

# Make script executable
RUN chmod +x /workspace/run_verify.sh

# Run the pipeline
ENTRYPOINT ["/workspace/run_verify.sh"]
