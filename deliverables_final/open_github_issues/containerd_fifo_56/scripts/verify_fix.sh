#!/bin/bash
set -e

# 1. Setup workspace
mkdir -p verification_env
cd verification_env

# 2. Clone the specific repository
git clone https://github.com/containerd/fifo.git repo
cd repo
# git checkout 0659fbd # Checking out the commit from your diff index

# 3. Save the patch to a file
# cat << 'EOF' > fix.patch
# --- a/fifo.go
# +++ b/fifo.go
# @@ -76,8 +76,10 @@
#  		// as that can confuse callers.
#  		return nil, err
#  	}
# -	return fifo, err
# -}
# +	if fifo.err != nil {
# +		fifo.Close()
# +		return nil, fifo.err
# +	}
# +	return fifo, nil
# +}
 
#  func openFifo(ctx context.Context, fn string, flag int, perm os.FileMode) (*fifo, error) {
# EOF

# 4. Apply the patch
echo "Applying patch..."
git apply ../../../fix.patch

# 5. Run verification via Docker
echo "Starting Docker verification..."
cat << 'EOF' > Dockerfile
FROM golang:1.21-bullseye
WORKDIR /app
COPY . .
RUN go mod download
RUN go build -o repro repro_issue.go
CMD ["./repro"]
EOF

# Copy the repro script into the repo folder for Docker access
cp ../../repro_issue.go .

docker build -t fifo-fix-verify .
docker run --rm fifo-fix-verify