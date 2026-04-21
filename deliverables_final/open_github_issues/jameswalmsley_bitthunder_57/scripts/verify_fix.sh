#!/bin/bash
# verify_fix.sh

# Exit immediately if a command exits with a non-zero status
set -e

REPO_URL="https://github.com/jameswalmsley/bitthunder.git"
PATCH_PATH="$(pwd)/fix.patch"

# 1. Check if patch file exists before starting
if [ ! -f "$PATCH_PATH" ]; then
    echo "ERROR: fix.patch not found at $PATCH_PATH"
    exit 1
fi

# 2. Clone the repository if it doesn't exist
if [ ! -d "bitthunder" ]; then
    echo "--- Cloning Repository ---"
    git clone $REPO_URL bitthunder
fi

cd bitthunder

# 3. Baseline check: Verify the issue exists (Missing return)
echo "--- Verifying issue presence (Expect warning) ---"
# We target the specific file to check for the return-type warning
arm-none-eabi-gcc -c os/src/bt_main.c -Ios/include -Wall -Wextra -o /dev/null 2>&1 | grep "control reaches end of non-void function" \
    && echo "CONFIRMED: Bug present." \
    || echo "CLEAN: No bug detected in current branch."

# 4. Apply your local fix.patch
echo "--- Applying local fix.patch ---"
git apply "$PATCH_PATH"

# 5. Verification: Check if the compiler is now happy
echo "--- Verifying fix (Expect no warning) ---"
if arm-none-eabi-gcc -c os/src/bt_main.c -Ios/include -Wall -Wextra -o /dev/null 2>&1 | grep "control reaches end of non-void function"; then
    echo "FAILED: The warning is still there."
    exit 1
else
    echo "SUCCESS: The return statement fixed the warning."
fi