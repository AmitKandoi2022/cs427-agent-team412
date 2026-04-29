#!/usr/bin/env bash
# Verifies the fix for zhewang2001/cs427-mp2 issue #2.
# Runs inside maven:3.9-eclipse-temurin-17 (same image as the agent).
# Usage: ./scripts/verify_fix.sh
set -euo pipefail

PATCH="$(cd "$(dirname "$0")/.." && pwd)/fix.patch"
WORKDIR=/tmp/cs427-mp2-verify

docker run --rm \
  -v "$PATCH:/fix.patch:ro" \
  maven:3.9-eclipse-temurin-17 \
  bash -c "
    set -euo pipefail
    apt-get update -qq && apt-get install -y -qq git python3 2>/dev/null

    echo '==> Cloning repository...'
    git clone --quiet https://github.com/zhewang2001/cs427-mp2.git $WORKDIR
    cd $WORKDIR

    echo '==> Applying patch...'
    git apply /fix.patch

    echo '==> Verifying compiler source/target set to 17...'
    grep -E 'maven\.compiler\.(source|target)>17' pom.xml | grep -c '17' | grep -q '^2$'

    echo '==> Running mvn clean install...'
    mvn clean install 2>&1 | grep -E '\[ERROR\]|\[INFO\] Tests run|BUILD' | tail -30
    mvn clean install -q

    echo '==> PASS: project builds and all tests pass under JDK 17.'
  "
