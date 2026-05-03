#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

git clone --depth 1 https://github.com/zhewang2001/Project.git "$WORK/repo"
git -C "$WORK/repo" apply "$DIR/../fix.patch"

if grep -RnE '"(Champaign|Chicago|Los Angeles)"' "$WORK/repo/app/src/main/java"; then
    echo "FAIL: hardcoded city literals still exist"
    exit 1
fi
echo "PASS: no hardcoded city literals"
