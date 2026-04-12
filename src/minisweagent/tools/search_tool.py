from dataclasses import dataclass, field
from typing import Any
import re
from . import register


@dataclass
class SearchFileContentTool:
    """
    search_file_content: Search a file for a pattern and return matching lines with context.

    Parameters:
    - path: str (file path)
    - query: str (pattern or keyword)
    - context_lines: int, optional, number of lines before/after match (default=2)

    Returns:
    - dict with keys:
        "returncode": 0 if successful, 1 if error
        "output": matched lines with context or error message
    """
    name: str = "search_file_content"
    description: str = "Search for a keyword or pattern in a file and return matching lines with context."
    parameters: dict = field(default_factory=lambda: {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file"},
            "query": {"type": "string", "description": "Text or regex pattern to search for"},
            "context_lines": {"type": "integer", "description": "Lines before/after match", "default": 2},
        },
        "required": ["path", "query"],
        "additionalProperties": False,
    })

    def __call__(self, args: dict, env: Any | None = None) -> dict:
        path = args["path"]
        query = args["query"]
        context_lines = args.get("context_lines", 2)

        try:
            # Use SWE-bench environment if available
            if env is not None:
                cmd = f"grep -n -C {context_lines} '{query}' {path} | head -n 100"
                result = env.execute(cmd)
                return {
                    "output": result["output"],
                    "returncode": result["returncode"],
                }

            # Local fallback
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            matches = []
            pattern = re.compile(query, re.IGNORECASE)
            for i, line in enumerate(lines):
                if pattern.search(line):
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    snippet = "".join(lines[start:end])
                    matches.append(f"[Line {i+1}]\n{snippet}")

            if not matches:
                return {"output": "No matches found.", "returncode": 0}

            return {"output": "\n".join(matches[:5]), "returncode": 0}  # limit to 5 matches

        except FileNotFoundError:
            return {"output": f"Error: File '{path}' not found.", "returncode": 1}
        except Exception as e:
            return {"output": f"Error: {str(e)}", "returncode": 1}


# Register the tool
register(SearchFileContentTool())