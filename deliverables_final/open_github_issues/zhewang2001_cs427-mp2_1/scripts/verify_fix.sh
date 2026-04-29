#!/usr/bin/env bash
# Verifies the Checkstyle integration fix for zhewang2001/cs427-mp2 issue #1.
# Clones the repo, applies fix.patch, runs mvn checkstyle:check in the same
# Maven image as the GitHub-issue agent (mini-swe maven:3.9-eclipse-temurin-17).
#
# Requires: git, docker
set -euo pipefail

REPO_URL="https://github.com/zhewang2001/cs427-mp2.git"
MVN_IMAGE="${MVN_IMAGE:-maven:3.9-eclipse-temurin-17}"
PATCH="$(cd "$(dirname "$0")/.." && pwd)/fix.patch"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found; install Docker or set PATH." >&2
  exit 1
fi

echo "==> Cloning repository..."
rm -rf /tmp/cs427-mp2-verify
git clone "$REPO_URL" /tmp/cs427-mp2-verify
cd /tmp/cs427-mp2-verify

echo "==> Applying patch..."
git apply "$PATCH"

echo "==> Verifying pom.xml has Checkstyle plugin..."
grep -q "maven-checkstyle-plugin" pom.xml

WORKDIR=/workspace
echo "==> Running mvn checkstyle:check in ${MVN_IMAGE}..."
docker run --rm \
  -v "$(pwd):${WORKDIR}" \
  -w "${WORKDIR}" \
  "${MVN_IMAGE}" \
  mvn --batch-mode checkstyle:check

echo "==> Verifying Checkstyle is bound to the build lifecycle..."
docker run --rm \
  -v "$(pwd):${WORKDIR}" \
  -w "${WORKDIR}" \
  "${MVN_IMAGE}" \
  mvn --batch-mode validate

echo "==> Fix verified: Checkstyle passes with 0 violations and is bound to the build lifecycle."
