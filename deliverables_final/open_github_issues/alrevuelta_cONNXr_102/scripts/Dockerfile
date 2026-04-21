FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential cmake git python3 python3-pip

RUN pip3 install onnx

WORKDIR /app

# 1. Clone the repo and move into it immediately
RUN git clone https://github.com/alrevuelta/cONNXr.git .

# 2. Create the reproduction model in the root
RUN echo "import onnx\n\
from onnx import helper, TensorProto\n\
def create():\n\
    node = helper.make_node('Constant', inputs=[], outputs=['out'])\n\
    graph = helper.make_graph([node], 'test', [], [helper.make_tensor_value_info('out', TensorProto.FLOAT, [1])])\n\
    model = helper.make_model(graph)\n\
    onnx.save(model, '/app/malformed.onnx')\n\
create()" > reproduce.py && python3 reproduce.py

# 3. Copy the patch
COPY fix.patch /app/fix.patch

# 4. Create the verification script
RUN echo "#!/bin/bash\n\
set -e\n\
\n\
echo '--- BUILDING UNPATCHED VERSION ---'\n\
# In-source build: run cmake and make right here\n\
cmake . && make\n\
\n\
echo '--- RUNNING UNPATCHED (EXPECT CRASH) ---'\n\
set +e\n\
./connxr /app/malformed.onnx\n\
RET_CODE=\$?\n\
set -e\n\
echo \"Unpatched exit code: \$RET_CODE (139 = Segfault)\"\n\
\n\
echo -e '\n--- APPLYING PATCH ---'\n\
git apply /app/fix.patch\n\
\n\
echo '--- REBUILDING PATCHED ---'\n\
# Re-run make to compile the changes\n\
make\n\
\n\
echo '--- RUNNING PATCHED (EXPECT SAFE EXIT) ---'\n\
set +e\n\
./connxr /app/malformed.onnx\n\
RESULT=\$?\n\
set -e\n\
\n\
if [ \$RESULT -eq 1 ]; then\n\
    echo 'SUCCESS: Patched version caught the NULL attribute and returned 1.'\n\
else\n\
    echo \"Verification ended with code \$RESULT (If 139, the fix failed)\"\n\
fi" > /app/run_verify.sh

RUN chmod +x /app/run_verify.sh

CMD ["/app/run_verify.sh"]