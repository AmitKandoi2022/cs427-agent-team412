#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/zhewang2001/Project.git"

echo "==> Cloning repository..."
rm -rf repo
git clone "$REPO_URL" repo

cd repo

echo "==> Running annotation verification..."
python /workspace/verify_fix.py

echo "==> Verification complete"
