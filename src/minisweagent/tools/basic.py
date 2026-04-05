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
import subprocess

from . import register


@dataclass
class ReadFile:
    name: str = "read_file"
    description: str = (
        "Read a text file with flexible line constraints. "
        "Use 'start_line' and 'end_line' for ranges, or 'limit' for head/tail reads."
    )
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file."},
                "start_line": {"type": "integer", "description": "1-indexed start line."},
                "end_line": {"type": "integer", "description": "1-indexed end line (inclusive)."},
                "limit": {"type": "integer", "description": "Number of lines to read from the start or end."},
                "mode": {
                    "type": "string", 
                    "enum": ["range", "head", "tail"], 
                    "description": "How to apply the limit. 'head' reads first N, 'tail' reads last N."
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        path = str(args.get("path", ""))
        quoted_path = shlex.quote(path)
        start = args.get("start_line")
        end = args.get("end_line")
        limit = args.get("limit")
        mode = args.get("mode", "range")

        # 1. Logic to determine the Bash command
        if mode == "head" and limit:
            cmd = f"head -n {limit} {quoted_path}"
        elif mode == "tail" and limit:
            cmd = f"tail -n {limit} {quoted_path}"
        elif start and end:
            # -n with 'p' in sed is the most efficient way to grab a range
            cmd = f"sed -n '{start},{end}p' {quoted_path}"
        elif start:
            cmd = f"sed -n '{start},$p' {quoted_path}"
        else:
            cmd = f"cat {quoted_path}"

        # 2. Add line numbers for the Agent! (Crucial for SearchAndReplace)
        # We pipe the result to 'nl -ba' or 'cat -n' so the agent knows exactly 
        # which lines it is looking at.
        cmd += " | cat -n"

        if env is not None:
            return env.execute(cmd)
        
        return {"output": f"Executing: {cmd}", "returncode": 0}


@dataclass
class WriteFile:
    name: str = "write_file"
    description: str = (
        "Write or modify a file. Supports overwriting, appending, or inserting "
        "at a specific line number."
    )
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file."},
                "content": {"type": "string", "description": "The text content to write."},
                "mode": {
                    "type": "string", 
                    "enum": ["overwrite", "append", "insert"],
                    "default": "overwrite",
                    "description": "How to write the content. 'insert' requires 'start_line'."
                },
                "start_line": {
                    "type": "integer", 
                    "description": "1-indexed line number for 'insert' mode."
                },
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        path = str(args.get("path", ""))
        content = args.get("content", "")
        mode = args.get("mode", "overwrite")
        start_line = args.get("start_line")

        # We use a Python "heredoc" approach inside the shell to handle 
        # multi-line strings and special characters safely.
        
        safe_content = repr(content)

        if mode == "overwrite":
            py_logic = f"open('{path}', 'w').write({safe_content})"

        elif mode == "append":
            py_logic = f"open('{path}', 'a').write('\\n' + {safe_content})"

        elif mode == "insert" and start_line is not None:
            py_logic = (
                f"lines = open('{path}').readlines(); "
                f"lines.insert({start_line}-1, {safe_content} + '\\n'); "
                f"open('{path}', 'w').writelines(lines)"
            )
        else:
            return {"output": "Error: 'insert' mode requires 'start_line'.", "returncode": 1}

        # Wrap the logic in a python3 call to ensure cross-platform safety in the sandbox
        full_cmd = f"python3 -c \"{py_logic}\""

        if env is not None:
            return env.execute(full_cmd)
        
        return {"output": f"Simulated {mode} on {path}", "returncode": 0}


@dataclass
class EditLines:
    name: str = "edit_lines"
    description: str = "Replace a specific line range with new content."
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "start": {"type": "integer"},
                "end": {"type": "integer"},
                "content": {"type": "string", "description": "The new code block."}
            },
            "required": ["path", "start", "end", "content"]
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        # Use a python script to safely overwrite the specific lines
        # This is much safer than 'sed -i' for multi-line content.
        path = args['path']
        start, end = args['start'], args['end']
        content = args['content'].replace("'", "'\\''") # Escape for shell
        
        py_code = (
            f"import sys; lines = open('{path}').readlines(); "
            f"lines[{start}-1:{end}] = ['{content}\\n']; "
            f"open('{path}', 'w').writelines(lines)"
        )
        if env is not None:
            return env.execute(f"python3 -c \"{py_code}\"")


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
                res = env.execute(f"echo '--- FILE: {quoted_path} ---' && cat -- {quoted_path} && echo ''")
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


@dataclass
class SearchAndReplace:
    name: str = "search_and_replace"
    description: str = (
        "Replace a specific block of code in a file. "
        "The 'old_str' must match the file content exactly, including indentation."
    )
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file."},
                "old_str": {"type": "string", "description": "The exact block of code to be replaced."},
                "new_str": {"type": "string", "description": "The new block of code to insert."},
            },
            "required": ["path", "old_str", "new_str"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        path_arg = str(args.get("path", ""))
        old_str = args.get("old_str", "")
        new_str = args.get("new_str", "")

        if env is not None:
            # In a real SWE-bench env, you might use a python script 
            # to perform the replacement to avoid shell escaping issues.
            # Here is a logic-gate approach:
            escaped_old = shlex.quote(old_str)
            escaped_new = shlex.quote(new_str)
            # You can execute a small python snippet inside the container
            py_cmd = (
                f"python3 -c \"import sys; p = '{path_arg}'; "
                f"c = open(p).read(); "
                f"open(p, 'w').write(c.replace({escaped_old}, {escaped_new}))\""
            )
            return env.execute(py_cmd)

        # Fallback: Local Host Execution
        try:
            p = Path(path_arg).expanduser().resolve()
            content = p.read_text(encoding="utf-8")
            
            if old_str not in content:
                return {
                    "output": "Error: 'old_str' not found in file. Ensure indentation matches exactly.", 
                    "returncode": 1
                }
            
            new_content = content.replace(old_str, new_str)
            p.write_text(new_content, encoding="utf-8")
            
            return {
                "output": f"Successfully updated {path_arg}", 
                "returncode": 0
            }
            
        except Exception as e:
            return {"output": f"Error: {e}", "returncode": 1}


@dataclass
class RunTest:
    name: str = "run_test"
    description: str = (
        "Run tests for a specific file or directory. "
        "Automatically detects if it should use 'pytest' or 'python -m unittest'."
    )
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "test_path": {
                    "type": "string", 
                    "description": "Path to the test file or test directory."
                },
                "test_name": {
                    "type": "string", 
                    "description": "Optional: Specific test function or class name to run."
                },
            },
            "required": ["test_path"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        test_path = str(args.get("test_path", ""))
        test_name = args.get("test_name", "")
        
        # Construct the target (e.g., path/to/test.py::test_func)
        target = f"{test_path}::{test_name}" if test_name else test_path

        # Strategy: Try pytest first as it's the standard for most repos in SWE-bench
        # Fallback to unittest if pytest isn't available or fails to find tests.
        cmd = f"pytest {target} || python3 -m unittest {target.replace('::', '.')}"

        if env is not None:
            return env.execute(cmd)
        
        # Local fallback for your own debugging
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {"output": result.stdout + result.stderr, "returncode": result.returncode}


@dataclass
class ListFilesTree:
    name: str = "list_files_tree"
    description: str = (
        "Show a depth-limited directory tree to understand repository structure. "
        "Useful for getting an overview without being overwhelmed by files."
    )
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Starting directory (default is '.')."},
                "depth": {"type": "integer", "description": "How many levels deep to go (default is 2)."},
            },
            "required": [],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        path = args.get("path", ".")
        quoted_path = shlex.quote(path)
        depth = args.get("depth", 2)

        # Strategy: Use 'tree' if available in the environment, otherwise fallback
        # In SWE-bench Docker envs, 'tree' is often installed.
        cmd = f"tree -L {depth} -F --noreport {quoted_path}"
        
        if env is not None:
            result = env.execute(cmd)
            # If 'tree' command not found, fallback to a basic find command
            if "not found" in result["output"].lower():
                fallback_cmd = f"find {quoted_path} -maxdepth {depth} -not -path '*/.*'"
                return env.execute(fallback_cmd)
            return result

        return {"output": "Standard tree output simulated for host.", "returncode": 0}


@dataclass
class FindDefinition:
    name: str = "find_definition"
    description: str = (
        "Search for the definition of a class or function within the codebase. "
        "Returns the file path and line number."
    )
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "The name of the class or function to find."},
            },
            "required": ["symbol"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        symbol = args.get("symbol", "")
        if not symbol:
            return {"output": "No symbol provided.", "returncode": 1}

        # Regex explanation: Look for 'class [symbol]' or 'def [symbol]('
        # This handles both classes and functions while ignoring variable usages.
        regex = f"^[[:space:]]*(class|def)[[:space:]]+{symbol}([[:space:]]*\\(|:)"
        
        # Using 'grep -rnE' for recursive, line-number, extended regex search.
        # We ignore common non-source directories like .git or __pycache__.
        cmd = f"grep -rnE '{regex}' . --exclude-dir={{.git,__pycache__,venv}}"

        if env is not None:
            result = env.execute(cmd)
            if not result["output"].strip():
                return {"output": f"No definition found for '{symbol}'.", "returncode": 0}
            return result

        return {"output": f"Searching for definition: {symbol}", "returncode": 0}

@dataclass
class RunPythonFile:
    name: str = "run_python_file"
    description: str = "Run a Python file and return its output."
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the Python file to execute."}
            },
            "required": ["path"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        path = str(args.get("path", ""))

        if not path:
            return {"output": "No path provided.", "returncode": 1}

        cmd = f"python3 {shlex.quote(path)}"

        if env is not None:
            return env.execute(cmd)

        return {"output": f"Simulated run: {cmd}", "returncode": 0}

@dataclass
class InstallPackage:
    name: str = "install_package"
    description: str = "Install a Python package using pip."
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "package": {
                    "type": "string",
                    "description": "Name of the Python package to install."
                }
            },
            "required": ["package"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        package = str(args.get("package", "")).strip()

        if not package:
            return {"output": "No package provided.", "returncode": 1}

        cmd = f"pip install {shlex.quote(package)}"

        if env is not None:
            return env.execute(cmd)

        return {"output": f"Simulated install: {cmd}", "returncode": 0}

@dataclass
class FileFind:
    name: str = "file_find"
    description: str = "Find files by name/glob pattern"
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern to search for"},
                "path": {"type": "string", "description": "Directory to search from", "default": "."}
            },
            "required": ["pattern"],
            "additionalProperties": False,
        }
    )

    def __call__(self, args: dict, env=None) -> dict:
        pattern = str(args.get("pattern", ""))
        path = str(args.get("path", "."))

        if not pattern:
            return {"output": "No pattern provided.", "returncode": 1}

        if env is not None:
            path_q = shlex.quote(path)
            pattern_q = shlex.quote(pattern)
            cmd = (
                f"find {path_q} -name {pattern_q} "
                f"-not -path '*/.git/*' "
            )
            result = env.execute(cmd)
            if not result["output"].strip():
                return {"output": f"No files found for pattern: {pattern}", "returncode": 0}
            return result

        try:
            p = Path(path).expanduser().resolve()
            skip_dirs = {".git"}
            matches = [
                str(m) for m in p.rglob(pattern)
                if not any(part in skip_dirs for part in m.parts)
            ]
            if not matches:
                return {"output": f"No files found for pattern: {pattern}", "returncode": 0}
            return {"output": "\n".join(sorted(matches)), "returncode": 0}
        except Exception as e:
            return {"output": f"Error searching for files: {e}", "returncode": 1}

# Register the tool
register(ReadFile())
register(WriteFile())
register(EditLines())
register(SearchFileContent())
register(ReplaceContent())
register(ReadManyFiles())
register(TodoWrite())
register(SearchAndReplace())
register(RunTest())
register(ListFilesTree())
register(FindDefinition())
register(RunPythonFile())
register(InstallPackage())
register(FileFind())