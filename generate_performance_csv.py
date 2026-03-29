import sys
import json
import csv


def main():
    # sys.argv[0] is the script name, sys.argv[1] is the first argument
    if len(sys.argv) < 2:
        print("Usage: python generate_performance_csv.py <file_path>")
        return

    try:
        file_path = sys.argv[1]
        # print(f"Opening file at: {file_path}")
        output_path = "./perf_output.csv"
        with (
            open(file_path, "r") as f,
            open(output_path, "w") as out
        ):
            data = json.load(f)
            writer = csv.writer(out)
            writer.writerow(["Instance ID", "Status"])
            for ins in data.get("completed_ids", []):
                if ins in data["resolved_ids"]:
                    writer.writerow([ins, "Resolved"])
                else:
                    writer.writerow([ins, "Failed"])
        print(f"Generated performance table in {output_path}")
    except Excpetion as e:
        print(str(e))
        

if __name__ == "__main__":
    main()


