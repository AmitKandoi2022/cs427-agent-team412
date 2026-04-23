#!/bin/bash
set -e

# build
make clean || true
make

# download PoC if not exists
if [ ! -f heap-overflow-adc-66 ]; then
    wget -q https://github.com/Lekensteyn/dmg2img/files/5010447/heap-overflow-adc-66.zip
    unzip -o heap-overflow-adc-66.zip
fi

# run test
./dmg2img -i ./heap-overflow-adc-66 -o /dev/null

echo "Program exited successfully (no crash)"
