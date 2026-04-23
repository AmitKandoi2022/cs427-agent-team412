# Use official Go image
FROM golang:1.24

# Install git and patch utility
RUN apt-get update && apt-get install -y git patch && rm -rf /var/lib/apt/lists/*

# Set working directory, clone repo
WORKDIR /go/src/github.com/moby/swarmkit
RUN git clone https://github.com/moby/swarmkit.git .

# Copy local patch into container
COPY fix.patch /tmp/fix.patch

# Apply the patch
RUN sed -i 's/context.Background()/ctx/' manager/state/raft/transport/peer.go

CMD ["go", "test", "./...", "-count=1", "-v"]