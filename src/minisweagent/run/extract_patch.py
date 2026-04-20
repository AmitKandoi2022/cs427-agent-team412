import codecs
import json
import sys


def write_clean_patch(patch_str, txt_output_path):
    try:
        clean_patch = codecs.decode(patch_str, 'unicode_escape')

        with open(txt_output_path, "w", encoding='utf-8') as f:
            f.write(clean_patch)
        print(f"Successfully wrote patch to {txt_output_path}")
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_patch.py <traj.json path> <fix.patch output path>")
        sys.exit(1)

    json_input_path = sys.argv[1]
    txt_output_path = sys.argv[2]

    with open(json_input_path, "r", encoding='utf-8') as f:
        data = json.load(f)
    
    
    patch_str = data["info"].get("submission", "")
    write_clean_patch(patch_str, txt_output_path)
