# backend/__init__.py
"""
LLMS File Builder Backend
"""
from .llms_processor import LLMSProcessor
from .csv_processor import CSVProcessor
from .categorizer import Categorizer
from .llms_generator import LLMSGenerator

__all__ = [
    'LLMSProcessor',
    'CSVProcessor', 
    'Categorizer',
    'LLMSGenerator'
]

# Updated run.py to use new backend
"""
# run.py
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path if needed
sys.path.insert(0, str(Path(__file__).parent))

from backend import LLMSProcessor

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(
        description="LLMS File Builder - Convert Screaming Frog exports to LLMS.txt files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run.py data/crawl.csv
  python run.py data/crawl.csv --use-gpt
  python run.py data/crawl.csv --preview
  python run.py data/crawl.csv --output mysite_llms
        '''
    )
    
    parser.add_argument(
        "csv_path",
        help="Path to Screaming Frog CSV export"
    )
    
    parser.add_argument(
        "--use-gpt",
        action="store_true",
        help="Use GPT for intelligent categorization (requires OpenAI API key)"
    )
    
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview output without saving files"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Custom output filename (without extension)"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the CSV file without processing"
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    if not Path(args.csv_path).exists():
        print(f"Error: File not found: {args.csv_path}")
        sys.exit(1)
    
    # Initialize processor
    processor = LLMSProcessor(use_gpt=args.use_gpt)
    
    # Validate only mode
    if args.validate_only:
        print(f"Validating {args.csv_path}...")
        result = processor.validate_csv(args.csv_path)
        
        if result['valid']:
            print("✓ CSV file is valid!")
            print(f"  Total rows: {result['total_rows']}")
            print(f"  File size: {result['file_size_mb']:.1f} MB")
            print(f"  Required columns: {len(result['columns']['required_present'])}")
            print(f"  Optional columns: {len(result['columns']['optional_present'])}")
        else:
            print(f"✗ Validation failed: {result['error']}")
            if 'available_columns' in result:
                print(f"  Available columns: {', '.join(result['available_columns'][:5])}...")
        return
    
    # Process file
    print(f"Processing {args.csv_path}...")
    if args.use_gpt:
        print("Using GPT for categorization...")
    
    result = processor.process_file(
        args.csv_path,
        preview_only=args.preview,
        custom_filename=args.output
    )
    
    if result['success']:
        print("✓ Processing complete!")
        
        # Show stats
        print(f"\nStatistics:")
        print(f"  Total rows in CSV: {result['stats']['total_rows']}")
        print(f"  Indexable pages: {result['stats']['indexable_pages']}")
        print(f"  Unique pages: {result['stats']['unique_pages']}")
        
        print(f"\nCategories:")
        for category, count in result['categories'].items():
            print(f"  {category}: {count} pages")
        
        if args.preview:
            print(f"\n--- Preview ---")
            print(result['preview'])
        else:
            print(f"\nFiles saved:")
            print(f"  LLMS.txt: {result['files']['txt_path']}")
            print(f"  LLMS.json: {result['files']['json_path']}")
            
            if result.get('validation_issues'):
                print(f"\nWarnings:")
                for issue in result['validation_issues']:
                    print(f"  ⚠ {issue}")
    else:
        print(f"✗ Processing failed: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""