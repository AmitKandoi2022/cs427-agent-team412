#!/bin/bash
set -e

# 1. Clone the repo
git clone https://github.com/LibVNC/libvncserver.git repo
cd repo
# git checkout 3387d166 # Checkout the base commit from the patch

# 2. Apply patch
git apply ../../fix.patch

# 3. Create Dockerfile
cat << 'EOF' > Dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    build-essential cmake git libssl-dev zlib1g-dev

WORKDIR /app
COPY . .

# 1. Build and Install to a local 'dist' folder
RUN mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/app/dist .. && \
    make -j$(nproc) && \
    make install

# 2. Create the repro script
RUN cat << 'EOT' > repro.c
#include <rfb/rfb.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>

int main() {
    // Open files to push next FD above 1024
    for (int i = 0; i < 1050; i++) {
        open("/dev/null", O_RDONLY);
    }

    rfbScreenInfoPtr screen = rfbGetScreen(0, NULL, 100, 100, 8, 3, 4);
    if (!screen) return 1;

    printf("Listener Pipe FD: %d\n", screen->pipe_notify_listener_thread[0]);
    return 0;
}
EOT

# 3. Compile using the standard install paths
# Note: libvncserver depends on helper libs, so we link them all
RUN gcc repro.c -o repro \
    -I/app/dist/include \
    -L/app/dist/lib \
    -lvncserver -lpthread -lssl -lcrypto -lz -lm

# 4. Set runtime library path
ENV LD_LIBRARY_PATH=/app/dist/lib:$LD_LIBRARY_PATH

CMD ["./repro"]
EOF

# 4. Run verification
docker build -t vnc-verify .
docker run --rm vnc-verify