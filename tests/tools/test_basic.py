import json
from pathlib import Path


def test_register_and_use_read_write_file(tmp_path):
    # Import registers tools into REGISTRY
    from minisweagent.tools import REGISTRY
    import minisweagent.tools.basic  # noqa: F401

    assert "read_file" in REGISTRY
    assert "write_file" in REGISTRY

    write = REGISTRY["write_file"]
    read = REGISTRY["read_file"]

    target = tmp_path / "example.txt"
    content = "hello world"

    # Write
    res_w = write({"path": str(target), "content": content})
    assert res_w["returncode"] == 0
    assert target.exists()
    assert target.read_text(encoding="utf-8") == content

    # Read
    res_r = read({"path": str(target)})
    assert res_r["returncode"] == 0
    assert res_r["output"] == content


def test_read_nonexistent(tmp_path):
    from minisweagent.tools import REGISTRY
    import minisweagent.tools.basic  # noqa: F401

    read = REGISTRY["read_file"]
    res = read({"path": str(tmp_path / "nope.txt")})
    assert res["returncode"] != 0
    assert "not found" in res["output"].lower()

