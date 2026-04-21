import onnx
from onnx import helper, TensorProto

def create_malformed_model():
    # Define a Constant node without the 'value' attribute
    # This is technically invalid ONNX, which is perfect for testing robustness
    node_def = helper.make_node(
        'Constant',
        inputs=[],
        outputs=['out'],
        # 'value' attribute is intentionally missing
    )

    graph_def = helper.make_graph(
        [node_def],
        'test-model',
        [],
        [helper.make_tensor_value_info('out', TensorProto.FLOAT, [1])],
    )

    model_def = helper.make_model(graph_def, producer_name='onnx-example')
    onnx.save(model_def, 'malformed_constant.onnx')
    print("Malformed model 'malformed_constant.onnx' created.")

if __name__ == "__main__":
    create_malformed_model()