# run_simple.py
"""
Simplified run script that skips the new validation features
Just processes the CSV file directly
"""
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))

from backend import LLMSProcessor

load_dotenv()

def main():
    parser = argparse.ArgumentParser(
        description="LLMS File Builder - Convert Screaming Frog exports to LLMS.txt files"
    )
    
    parser.add_argument("csv_path", help="Path to Screaming Frog CSV export")
    parser.add_argument("--use-gpt", action="store_true", help="Use GPT for categorization")
    parser.add_argument("--output", type=str, help="Custom output filename")
    
    args = parser.parse_args()
    
    # Check if file exists
    if not Path(args.csv_path).exists():
        print(f"❌ Error: File not found: {args.csv_path}")
        sys.exit(1)
    
    # Process directly
    print(f"Processing {args.csv_path}...")
    
    processor = LLMSProcessor(use_gpt=args.use_gpt)
    
    if args.use_gpt:
        print("🤖 Using GPT for categorization...")
    else:
        print("⚡ Using pattern-based categorization...")
    
    # Process the file
    result = processor.process_file(
        args.csv_path,
        custom_filename=args.output
    )
    
    if result.get('success'):
        print("\n✅ Success!")
        
        # Show categories
        if 'categories' in result:
            print("\n📁 Categories:")
            for cat, count in result['categories'].items():
                if count > 0:
                    print(f"  {cat}: {count} pages")
        
        # Show file paths
        if 'files' in result:
            print(f"\n📄 Files saved:")
            print(f"  {result['files']['txt_path']}")
            print(f"  {result['files']['json_path']}")
    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()