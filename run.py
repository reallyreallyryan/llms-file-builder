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

def print_export_instructions():
    """Print instructions for proper Screaming Frog export"""
    print("""
📋 How to Export from Screaming Frog for Best Results:

1. In Screaming Frog, click the 'Internal' tab (not 'All')
2. Click the Filter dropdown → Select 'HTML'
3. File → Export → Save as CSV

This ensures you export only actual web pages, not images or scripts!
""")

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
  python run.py data/crawl.csv --force
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
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Process even if CSV quality is poor"
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    if not Path(args.csv_path).exists():
        print(f"❌ Error: File not found: {args.csv_path}")
        sys.exit(1)
    
    # Initialize processor
    processor = LLMSProcessor(use_gpt=args.use_gpt)
    
    # Validate CSV quality
    print(f"Analyzing {args.csv_path}...")
    validation = processor.validate_csv(args.csv_path)  
      
    if not validation['valid']:
        print(f"❌ Error: {validation['error']}")
        if 'available_columns' in validation:
            print(f"\nAvailable columns: {', '.join(validation['available_columns'][:10])}...")
            print("\nMake sure you're exporting from Screaming Frog's 'Internal' tab")
        sys.exit(1)
    
    # Show analysis
    analysis = validation['analysis']
    print(f"\n📊 CSV Analysis:")
    print(f"  Total URLs: {analysis['total_urls']}")
    print(f"  Quality Score: {analysis['quality_score']:.0f}/100")
    
    # Show breakdown if there are issues
    if analysis['issues']:
        print(f"\n⚠️  Issues found:")
        for issue in analysis['issues']:
            print(f"  - {issue}")
    
    # Validate only mode
    if args.validate_only:
        if analysis['appears_filtered']:
            print("\n✅ CSV is properly filtered and ready for processing!")
        else:
            print(f"\n{validation['export_advice']}")
            print_export_instructions()
        return
    
    # Check quality and advise if needed
    if not analysis['appears_filtered'] and not args.force:
        print(f"\n{validation['export_advice']}")
        print("\n💡 Recommendation: Re-export with HTML filter for best results!")
        print("   Or use --force to process anyway\n")
        
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("\nExiting. Please re-export your CSV with proper filters.")
            print_export_instructions()
            sys.exit(0)
    
    # Calculate estimated pages after filtering
    estimated_content_pages = analysis['total_urls'] - analysis['non_content_count']
    
    # Process file
    print(f"\n🔄 Processing {estimated_content_pages} estimated content pages...")
    if args.use_gpt:
        # Estimate processing time (roughly 0.2 seconds per page for GPT)
        estimated_time = estimated_content_pages * 0.2
        print(f"🤖 Using GPT for categorization (estimated time: {estimated_time:.0f} seconds)...")
    else:
        print("⚡ Using pattern-based categorization (fast mode)...")
    
    result = processor.process_file(
        args.csv_path,
        preview_only=args.preview,
        custom_filename=args.output,
        force_processing=args.force
    )
    
    if result['success']:
        print("\n✅ Processing complete!")
        
        # Show stats
        stats = result['stats']
        print(f"\n📈 Statistics:")
        print(f"  Total rows in CSV: {stats['total_rows']}")
        print(f"  Indexable pages: {stats['indexable_pages']}")
        print(f"  Unique pages processed: {stats['unique_pages']}")
        
        # Show categories
        print(f"\n📁 Categories:")
        total_categorized = 0
        for category, count in sorted(result['categories'].items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                print(f"  {category}: {count} pages")
                total_categorized += count
        
        if args.preview:
            print(f"\n--- Preview ---")
            print(result['preview'])
            print("\n💡 Use without --preview to save the files")
        else:
            print(f"\n📄 Files saved:")
            print(f"  LLMS.txt: {result['files']['txt_path']}")
            print(f"  LLMS.json: {result['files']['json_path']}")
            
            if result.get('validation_issues'):
                print(f"\n⚠️  Minor issues:")
                for issue in result['validation_issues']:
                    print(f"  - {issue}")
            
            print(f"\n✨ Successfully processed {total_categorized} pages into LLMS.txt!")
    else:
        print(f"\n❌ Processing failed: {result['error']}")
        if result.get('error_type') == 'ValueError':
            print("\n💡 This might be a data format issue. Try:")
            print("  1. Re-export from Screaming Frog with 'Internal' → 'HTML' filter")
            print("  2. Check that your CSV has the required columns")
        sys.exit(1)

if __name__ == "__main__":
    main()