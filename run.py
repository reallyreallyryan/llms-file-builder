
import argparse
from main import run_tool

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LLMS File Builder")
    parser.add_argument("--csv_path", type=str, required=True, help="Path to Screaming Frog CSV export")
    parser.add_argument("--use_gpt", action="store_true", help="Use GPT to generate structured LLMS output")

    args = parser.parse_args()

    result = run_tool({
        "csv_path": args.csv_path,
        "use_gpt": args.use_gpt
    })

    print(result)
