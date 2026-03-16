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


# @dataclass
# class ReadFile:
#     name: str = "read_file"
#     description: str = "Read a UTF-8 text file."
#     parameters: dict = field(
#         default_factory=lambda: {
#             "type": "object",
#             "properties": {
#                 "path": {"type": "string", "description": "Path to the file to read"},
#             },
#             "required": ["path"],
#             "additionalProperties": False,
#         }
#     )

#     def __call__(self, args: dict, env=None) -> dict:
#         path_arg = str(args.get("path", ""))
#         # If an environment is provided, run inside it so reads happen in the sandbox (e.g., /testbed)
#         if env is not None:
#             if not path_arg:
#                 return {"output": "Missing 'path'", "returncode": 2}
#             cmd = f"cat -- {shlex.quote(path_arg)}"
#             return env.execute(cmd)
#         # Fallback: host filesystem read
#         try:
#             p = Path(path_arg).expanduser().resolve()
#             content = p.read_text(encoding="utf-8", errors="replace")
#             return {"output": content, "returncode": 0}
#         except FileNotFoundError:
#             return {"output": f"File not found: {path_arg}", "returncode": 2}
#         except IsADirectoryError:
#             return {"output": f"Is a directory: {path_arg}", "returncode": 21}
#         except PermissionError:
#             return {"output": f"Permission denied: {path_arg}", "returncode": 13}
#         except Exception as e:  # pragma: no cover - generic safety net
#             return {"output": f"Error reading file: {e}", "returncode": 1}


@dataclass
class ReadFile:
    name: str = "read_file"
    description: str = "Read a UTF-8 text file with optional line constraints."
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to read"},
                "start_line": {"type": "integer", "description": "First line to read (1-indexed)."},
                "end_line": {"type": "integer", "description": "Last line to read (inclusive)."},
            },
            "required": ["path"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        path_arg = str(args.get("path", ""))
        start = args.get("start_line")
        end = args.get("end_line")

        if not path_arg:
            return {"output": "Missing 'path'", "returncode": 2}

        # 1. Sandbox Execution (Docker/Testbed) using 'sed'
        if env is not None:
            quoted_path = shlex.quote(path_arg)
            if start is not None and end is not None:
                cmd = f"sed -n '{start},{end}p' -- {quoted_path}"
            elif start is not None:
                cmd = f"sed -n '{start},$p' -- {quoted_path}"
            elif end is not None:
                cmd = f"sed -n '1,{end}p' -- {quoted_path}"
            else:
                cmd = f"cat -- {quoted_path}"
            return env.execute(cmd)

        # 2. Fallback: Host Filesystem
        try:
            p = Path(path_arg).expanduser().resolve()
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            
            # Apply slicing (convert 1-indexing to 0-indexing)
            s_idx = (start - 1) if start is not None else 0
            e_idx = end if end is not None else len(lines)
            
            content = "\n".join(lines[s_idx:e_idx])
            return {"output": content, "returncode": 0}
            
        except FileNotFoundError:
            return {"output": f"File not found: {path_arg}", "returncode": 2}
        except Exception as e:
            return {"output": f"Error reading file: {e}", "returncode": 1}

# @dataclass
# class WriteFile:
#     name: str = "write_file"
#     description: str = "Write content to a UTF-8 text file, creating parent directories if needed."
#     parameters: dict = field(
#         default_factory=lambda: {
#             "type": "object",
#             "properties": {
#                 "path": {"type": "string", "description": "Path to the file to write."},
#                 "content": {"type": "string", "description": "The text content to write into the file."},
#             },
#             "required": ["path", "content"],
#             "additionalProperties": False,
#         }
#     )

#     def __call__(self, args: dict, env=None) -> dict:
#         path_arg = str(args.get("path", ""))
#         content_arg = str(args.get("content", ""))

#         if not path_arg:
#             return {"output": "Missing 'path'", "returncode": 2}

#         # Sandbox execution via environment (Docker/Testbed)
#         if env is not None:
#             # We use a shell-safe way to write content. 
#             # 'cat << 'EOF' > path' is generally safer for multi-line content than 'echo'.
#             # shlex.quote handles the path, but content needs careful escaping.
#             quoted_path = shlex.quote(path_arg)
            
#             # Ensure the directory exists first in the sandbox
#             dir_cmd = f"mkdir -p -- $(dirname -- {quoted_path})"
#             env.execute(dir_cmd)

#             # Write the file using a heredoc to preserve formatting/special characters
#             write_cmd = f"cat << 'EOF' > {quoted_path}\n{content_arg}\nEOF"
#             return env.execute(write_cmd)

#         # Fallback: Host filesystem write
#         try:
#             p = Path(path_arg).expanduser().resolve()
#             p.parent.mkdir(parents=True, exist_ok=True)
#             p.write_text(content_arg, encoding="utf-8")
#             return {"output": f"Successfully wrote to {path_arg}", "returncode": 0}
#         except IsADirectoryError:
#             return {"output": f"Is a directory: {path_arg}", "returncode": 21}
#         except PermissionError:
#             return {"output": f"Permission denied: {path_arg}", "returncode": 13}
#         except Exception as e:
#             return {"output": f"Error writing file: {e}", "returncode": 1}

@dataclass
class WriteFile:
    name: str = "write_file"
    description: str = "Write content to a file. Supports overwriting the whole file or inserting at a specific line."
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file."},
                "content": {"type": "string", "description": "The text content to write or insert."},
                "insert_line": {
                    "type": "integer", 
                    "description": "Optional: 1-indexed line number where content should be inserted. If omitted, the file is overwritten."
                },
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        path_arg = str(args.get("path", ""))
        content = str(args.get("content", ""))
        insert_line = args.get("insert_line")

        if not path_arg:
            return {"output": "Missing 'path'", "returncode": 2}

        # 1. Sandbox Execution (Docker/Testbed) using 'sed'
        if env is not None:
            quoted_path = shlex.quote(path_arg)
            if insert_line is not None:
                # 'sed -i' for in-place edit. 'Ni' inserts before line N.
                # We escape single quotes in content for the shell.
                escaped_content = content.replace("'", "'\\''")
                cmd = f"sed -i '{insert_line}i {escaped_content}' {quoted_path}"
            else:
                # Standard overwrite with directory creation
                dir_cmd = f"mkdir -p -- $(dirname -- {quoted_path})"
                env.execute(dir_cmd)
                cmd = f"cat << 'EOF' > {quoted_path}\n{content}\nEOF"
            return env.execute(cmd)

        # 2. Fallback: Host Filesystem
        try:
            p = Path(path_arg).expanduser().resolve()
            
            if insert_line is not None:
                if not p.exists():
                    return {"output": "File must exist to perform line insertion.", "returncode": 2}
                
                lines = p.read_text(encoding="utf-8").splitlines()
                # Adjust for 1-indexing: insert at (line - 1)
                idx = max(0, insert_line - 1)
                lines.insert(idx, content)
                p.write_text("\n".join(lines) + "\n", encoding="utf-8")
                return {"output": f"Inserted content at line {insert_line} in {path_arg}", "returncode": 0}
            
            else:
                # Standard overwrite logic
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
                return {"output": f"Successfully wrote to {path_arg}", "returncode": 0}

        except Exception as e:
            return {"output": f"Error writing file: {e}", "returncode": 1}
            

@dataclass
class SearchFileContent:
    name: str = "search_file_content"
    description: str = "Search for a regex pattern in a file and return matching lines with context."
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to search."},
                "pattern": {"type": "string", "description": "The regex pattern to search for."},
                "context_lines": {
                    "type": "integer", 
                    "description": "Number of lines to show before and after each match.",
                    "default": 2
                },
            },
            "required": ["path", "pattern"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        path_arg = str(args.get("path", ""))
        pattern = str(args.get("pattern", ""))
        context = args.get("context_lines", 2)

        if not path_arg or not pattern:
            return {"output": "Missing 'path' or 'pattern'", "returncode": 2}

        # 1. Sandbox Execution (Docker/Testbed) using grep
        if env is not None:
            quoted_path = shlex.quote(path_arg)
            # -n: show line numbers
            # -E: interpret pattern as extended regex
            # -C: show context lines before and after
            cmd = f"grep -nEC {context} -- {shlex.quote(pattern)} {quoted_path}"
            result = env.execute(cmd)
            
            # Grep returns 1 if no matches are found; we should make that clear to the agent
            if result["returncode"] == 1:
                return {"output": f"No matches found for pattern: {pattern}", "returncode": 0}
            return result

        # 2. Fallback: Host Filesystem
        try:
            import re
            p = Path(path_arg).expanduser().resolve()
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            
            output_parts = []
            for i, line in enumerate(lines):
                if re.search(pattern, line):
                    # Calculate range with bounds checking
                    start = max(0, i - context)
                    end = min(len(lines), i + context + 1)
                    
                    match_segment = []
                    for idx in range(start, end):
                        prefix = "> " if idx == i else "  "
                        match_segment.append(f"{idx + 1}:{prefix}{lines[idx]}")
                    
                    output_parts.append("\n".join(match_segment))
                    output_parts.append("-" * 20)

            if not output_parts:
                return {"output": f"No matches found for pattern: {pattern}", "returncode": 0}
                
            return {"output": "\n".join(output_parts), "returncode": 0}
            
        except Exception as e:
            return {"output": f"Error searching file: {e}", "returncode": 1}


@dataclass
class ReplaceContent:
    name: str = "replace_content"
    description: str = "Replace text in a file using string matching or by applying a unified diff patch."
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to modify."},
                "old_str": {"type": "string", "description": "The exact string to be replaced."},
                "new_str": {"type": "string", "description": "The string to replace it with."},
                "diff": {"type": "string", "description": "A unified diff format patch to apply."},
            },
            "required": ["path"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        path_arg = str(args.get("path", ""))
        old_str = args.get("old_str")
        new_str = args.get("new_str")
        diff_patch = args.get("diff")

        if not path_arg:
            return {"output": "Missing 'path'", "returncode": 2}

        # 1. Sandbox Execution (Docker/Testbed)
        if env is not None:
            quoted_path = shlex.quote(path_arg)
            
            # Case A: Apply a Diff Patch (The preferred way for agents)
            if diff_patch:
                # Use a heredoc to pass the diff to the 'patch' command
                cmd = f"patch {quoted_path} << 'EOF'\n{diff_patch}\nEOF"
                return env.execute(cmd)
            
            # Case B: String Replacement using 'sed'
            elif old_str is not None and new_str is not None:
                # Use a specific delimiter (|) in case the strings contain slashes (common in code/paths)
                escaped_old = old_str.replace("'", "'\\''")
                escaped_new = new_str.replace("'", "'\\''")
                cmd = f"sed -i 's|{escaped_old}|{escaped_new}|g' {quoted_path}"
                return env.execute(cmd)
            
            return {"output": "Provide either (old_str and new_str) or a diff.", "returncode": 2}

        # 2. Fallback: Host Filesystem
        try:
            p = Path(path_arg).expanduser().resolve()
            content = p.read_text(encoding="utf-8")

            if diff_patch:
                # Note: For host fallback, you'd typically use a library like 'patch-ng' 
                # or subprocess call to system 'patch'.
                return {"output": "Diff patching not implemented in host fallback. Use string replacement.", "returncode": 1}
            
            if old_str in content:
                new_content = content.replace(old_str, new_str)
                p.write_text(new_content, encoding="utf-8")
                return {"output": f"Successfully replaced occurrences in {path_arg}", "returncode": 0}
            else:
                return {"output": "The string to replace was not found in the file.", "returncode": 1}

        except Exception as e:
            return {"output": f"Error modifying file: {e}", "returncode": 1}


@dataclass
class ReadManyFiles:
    name: str = "read_many_files"
    description: str = "Read the content of multiple files at once. Returns a concatenated string with clear file headers."
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "A list of file paths to read."
                },
            },
            "required": ["paths"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        paths = args.get("paths", [])
        if not paths:
            return {"output": "No paths provided.", "returncode": 2}

        output_segments = []
        overall_returncode = 0

        for path_str in paths:
            # Re-using logic or calling a helper to handle the individual read
            if env is not None:
                quoted_path = shlex.quote(path_str)
                # Use a header to separate files in the combined output
                res = env.execute(f"echo '--- FILE: {path_str} ---' && cat -- {quoted_path} && echo ''")
                if res["returncode"] != 0:
                    overall_returncode = res["returncode"]
                output_segments.append(res["output"])
            else:
                # Fallback: Host filesystem
                try:
                    p = Path(path_str).expanduser().resolve()
                    content = p.read_text(encoding="utf-8", errors="replace")
                    output_segments.append(f"--- FILE: {path_str} ---\n{content}\n")
                except Exception as e:
                    output_segments.append(f"--- FILE: {path_str} ---\nError: {e}\n")
                    overall_returncode = 1

        return {
            "output": "\n".join(output_segments),
            "returncode": overall_returncode
        }


@dataclass
class TodoWrite:
    name: str = "todo_write"
    description: str = "Maintain and update a persistent TODO list to track task progress."
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string", 
                    "enum": ["add", "remove", "complete", "list"],
                    "description": "The action to perform on the TODO list."
                },
                "item": {
                    "type": "string", 
                    "description": "The task description (required for add, remove, and complete)."
                },
                "path": {
                    "type": "string", 
                    "description": "Path to the TODO file.",
                    "default": "TODO.md"
                },
            },
            "required": ["action"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        action = args.get("action")
        item = args.get("item", "")
        path_arg = args.get("path", "TODO.md")

        # Helper to read existing TODOs
        def read_todos(p: Path):
            if not p.exists(): return []
            return p.read_text().splitlines()

        # Helper to write TODOs
        def save_todos(p: Path, lines: list):
            p.write_text("\n".join(lines))

        try:
            p = Path(path_arg).expanduser().resolve()
            
            if action == "list":
                if not p.exists():
                    return {"output": "No TODO list found.", "returncode": 0}
                return {"output": p.read_text(), "returncode": 0}

            if not item:
                return {"output": f"Item description required for action '{action}'", "returncode": 2}

            lines = read_todos(p)

            if action == "add":
                lines.append(f"- [ ] {item}")
                save_todos(p, lines)
                return {"output": f"Added task: {item}", "returncode": 0}

            elif action == "complete":
                new_lines = []
                found = False
                for line in lines:
                    if item.lower() in line.lower() and "[ ]" in line:
                        new_lines.append(line.replace("[ ]", "[x]"))
                        found = True
                    else:
                        new_lines.append(line)
                if not found:
                    return {"output": f"Task containing '{item}' not found or already completed.", "returncode": 1}
                save_todos(p, new_lines)
                return {"output": f"Completed task: {item}", "returncode": 0}

            elif action == "remove":
                new_lines = [l for l in lines if item.lower() not in l.lower()]
                if len(new_lines) == len(lines):
                    return {"output": f"Task containing '{item}' not found.", "returncode": 1}
                save_todos(p, new_lines)
                return {"output": f"Removed task: {item}", "returncode": 0}

        except Exception as e:
            return {"output": f"Error updating TODO list: {e}", "returncode": 1}


# Register the tool
register(ReadFile())
register(WriteFile())
register(SearchFileContent())
register(ReplaceContent())
register(ReadManyFiles())
register(TodoWrite())