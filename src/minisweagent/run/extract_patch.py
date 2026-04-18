import json
import re
import sys


def extract_bash_sed_pattern(json_file_path: str) -> list:
    """
    Extracts patterns starting with ```bash\nsed -i and ending with ``` 
    from a specific key in a JSON file.
    """
    try:
        res = []
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Access the text content (handling nested keys if necessary)
        content_list = data.get("messages", "")
        if not content_list:
            return res

        pattern = r"```bash\n(sed -i.*?)(?=```)"
        for ele in content_list:
            text_content = ele.get("content")
            # Regex explanation:
            # ```bash\n       -> Matches the literal start tag
            # (sed -i.*?)      -> Captures 'sed -i' and everything after until...
            # (?=```)          -> A positive lookahead for the closing backticks
            # re.DOTALL        -> Allows the '.' to match newline characters
            
            matches = re.findall(pattern, text_content, re.DOTALL)
            # matches = re.findall(pattern, text_content)

            
            res += [match.strip() for match in matches]
        return res

    except (FilePathError, json.JSONDecodeError) as e:
        print(f"Error processing file: {e}")
        return []

# Example usage:
# If your JSON looks like: {"description": "Run this: ```bash\nsed -i 's/a/b/g' file.txt```"}
# matches = extract_bash_sed_pattern("data.json", "description")
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_patch.py <traj.json path> <fix.patch output path>")
        sys.exit(1)

    json_input_path = sys.argv[1]
    txt_output_path = sys.argv[2]

    res = extract_bash_sed_pattern(json_input_path)
    

    try:
        with open(txt_output_path, "w", encoding='utf-8') as f:
            for item in res:
                # Convert item to string and add a newline
                f.write(f"{item}\n")
        print(f"Successfully wrote {len(res)} rows to {txt_output_path}")
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")