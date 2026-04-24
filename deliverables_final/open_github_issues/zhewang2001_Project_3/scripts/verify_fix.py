import os
import re
import sys

ROOT = "app/src/main/java"

ANNOTATION_PATTERN = r"@(?:NonNull|Nullable|RecentlyNonNull|RecentlyNullable)"

CLASS_SKIP_PATTERN = re.compile(
    r"class\s+\w+\s+.*(Activity|Fragment)"
)

METHOD_PATTERN = re.compile(
    r"public\s+(?!class|interface)([^\(]+)\(([^)]*)\)"
)

ANNOTATED_RETURN_PATTERN = re.compile(
    rf"{ANNOTATION_PATTERN}\s+[\w<>\[\]]+\s+\w+\s*\("
)

PARAM_SPLIT_PATTERN = re.compile(r",(?![^\(]*\))")


def find_java_files():
    for root, _, files in os.walk(ROOT):
        for f in files:
            if f.endswith(".java"):
                yield os.path.join(root, f)


def is_activity_or_fragment(content):
    return bool(CLASS_SKIP_PATTERN.search(content))


def has_annotated_return(signature):
    return bool(ANNOTATED_RETURN_PATTERN.search(signature))


def check_parameters(params, file_path, line_no):
    errors = []

    if not params.strip():
        return errors

    parts = PARAM_SPLIT_PATTERN.split(params)

    for p in parts:
        p = p.strip()
        if not re.search(ANNOTATION_PATTERN, p):
            errors.append(
                f"{file_path}:{line_no} → Parameter missing annotation: '{p}'"
            )

    return errors


def check_file(path):
    errors = []

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    content = "".join(lines)

    if is_activity_or_fragment(content):
        return errors

    for i, line in enumerate(lines):
        if "public" not in line or "(" not in line:
            continue

        match = METHOD_PATTERN.search(line)
        if not match:
            continue

        signature = line.strip()
        params = match.group(2)

        # Check return annotation
        if not has_annotated_return(signature):
            errors.append(
                f"{path}:{i+1} → Missing return annotation: {signature}"
            )

        # Check parameters
        errors.extend(check_parameters(params, path, i + 1))

    return errors


def main():
    all_errors = []

    for file_path in find_java_files():
        all_errors.extend(check_file(file_path))

    if all_errors:
        print("Annotation verification failed:\n")
        for e in all_errors:
            print(e)
        sys.exit(1)
    else:
        print("All public methods are properly annotated")
        sys.exit(0)


if __name__ == "__main__":
    main()
