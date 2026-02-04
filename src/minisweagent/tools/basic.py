"""Basic, safe local tools: read_file and write_file.

Both tools are synchronous and return a dict matching the environment
execute result shape: {"output": str, "returncode": int}.

Safety considerations (kept simple on purpose for a starter set):
- Paths are resolved to absolute paths.
- write_file creates parent directories as needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shlex

from . import register


@dataclass
class ReadFile:
    name: str = "read_file"
    description: str = "Read a UTF-8 text file."
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to read"},
            },
            "required": ["path"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        path_arg = str(args.get("path", ""))
        # If an environment is provided, run inside it so reads happen in the sandbox (e.g., /testbed)
        if env is not None:
            if not path_arg:
                return {"output": "Missing 'path'", "returncode": 2}
            cmd = f"cat -- {shlex.quote(path_arg)}"
            return env.execute(cmd)
        # Fallback: host filesystem read
        try:
            p = Path(path_arg).expanduser().resolve()
            content = p.read_text(encoding="utf-8", errors="replace")
            return {"output": content, "returncode": 0}
        except FileNotFoundError:
            return {"output": f"File not found: {path_arg}", "returncode": 2}
        except IsADirectoryError:
            return {"output": f"Is a directory: {path_arg}", "returncode": 21}
        except PermissionError:
            return {"output": f"Permission denied: {path_arg}", "returncode": 13}
        except Exception as e:  # pragma: no cover - generic safety net
            return {"output": f"Error reading file: {e}", "returncode": 1}

# Register defaults on import for convenience
register(ReadFile())
