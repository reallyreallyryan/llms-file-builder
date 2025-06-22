# test_setup.py
"""
Test script to validate LLMS File Builder setup
"""
import os
import sys
import pandas as pd
from pathlib import Path

def create_test_csv():
    """Create a small test CSV file"""
    test_data = {
        'Address': [
            'https://example.com/',
            'https://example.com/services/therapy',
            'https://example.com/services/injections',
            'https://example.com/areas-we-treat/back-pain',
            'https://example.com/areas-we-treat/neck-pain',
            'https://example.com/blog/pain-management-tips',
            'https://example.com/blog/exercise-guide',
            'https://example.com/providers/dr-smith',
            'https://example.com/locations/phoenix',
            'https://example.com/about-us',
            'https://example.com/contact',
            'https://example.com/patient-forms'
        ],
        'Title 1': [
            'Example Medical Center - Pain Management Specialists',
            'Physical Therapy Services | Example Medical',
            'Injection Treatments for Pain Relief',
            'Back Pain Treatment Options',
            'Neck Pain Relief Solutions',
            '5 Tips for Managing Chronic Pain',
            'Best Exercises for Joint Health',
            'Dr. Jane Smith - Pain Management Physician',
            'Phoenix Location - Example Medical Center',
            'About Our Practice',
            'Contact Us',
            'Patient Forms and Resources'
        ],
        'Meta Description 1': [
            'Leading pain management center offering non-surgical treatments for chronic pain.',
            'Comprehensive physical therapy services to help you recover and maintain mobility.',
            'Advanced injection therapies including PRP and cortisone for pain relief.',
            'Effective non-surgical treatments for acute and chronic back pain.',
            'Get relief from neck pain with our specialized treatment programs.',
            'Learn practical strategies for managing chronic pain in daily life.',
            'Doctor-recommended exercises to improve joint health and flexibility.',
            'Board-certified pain management physician with 15 years experience.',
            'Visit our Phoenix location for comprehensive pain management care.',
            'Learn about our mission and approach to patient-centered care.',
            'Schedule an appointment or contact us with questions.',
            'Download patient forms and access helpful resources.'
        ],
        'Status Code': [200] * 12,
        'Indexability': ['Indexable'] * 12,
        'H1-1': [
            'Welcome to Example Medical Center',
            'Physical Therapy Services',
            'Pain Relief Injections',
            'Back Pain Treatment',
            'Neck Pain Treatment',
            'Managing Chronic Pain',
            'Exercise Guide',
            'Dr. Jane Smith',
            'Phoenix Location',
            'About Us',
            'Contact',
            'Patient Resources'
        ],
        'Word Count': [500, 800, 750, 900, 850, 1200, 1100, 600, 400, 700, 300, 500]
    }
    
    df = pd.DataFrame(test_data)
    
    # Create data directory
    os.makedirs('data/test', exist_ok=True)
    
    # Save test CSV
    csv_path = 'data/test/test_crawl.csv'
    df.to_csv(csv_path, index=False)
    
    return csv_path

def test_backend():
    """Test the backend modules"""
    print("Testing LLMS File Builder Setup...\n")
    
    # Test imports
    print("1. Testing imports...")
    try:
        from backend import LLMSProcessor, CSVProcessor, Categorizer, LLMSGenerator
        print("✓ All backend modules imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("  Make sure you've created the backend/ directory with all modules")
        return False
    
    # Test environment
    print("\n2. Testing environment...")
    from dotenv import load_dotenv
    load_dotenv()
    
    has_api_key = bool(os.getenv("OPENAI_API_KEY"))
    if has_api_key:
        print("✓ OpenAI API key found in environment")
    else:
        print("⚠ No OpenAI API key found (GPT features will be disabled)")
    
    # Create test data
    print("\n3. Creating test data...")
    csv_path = create_test_csv()
    print(f"✓ Test CSV created: {csv_path}")
    
    # Test CSV validation
    print("\n4. Testing CSV validation...")
    processor = LLMSProcessor()
    validation_result = processor.validate_csv(csv_path)
    
    if validation_result['valid']:
        print("✓ CSV validation passed")
        print(f"  - Rows: {validation_result['total_rows']}")
        print(f"  - Required columns: {len(validation_result['columns']['required_present'])}")
    else:
        print(f"✗ CSV validation failed: {validation_result['error']}")
        return False
    
    # Test pattern-based processing
    print("\n5. Testing pattern-based processing...")
    result = processor.process_file(csv_path, preview_only=True)
    
    if result['success']:
        print("✓ Pattern-based processing successful")
        print(f"  - Categories found: {len(result['categories'])}")
        for cat, count in result['categories'].items():
            print(f"    • {cat}: {count} pages")
    else:
        print(f"✗ Processing failed: {result['error']}")
        return False
    
    # Test GPT processing if API key available
    if has_api_key:
        print("\n6. Testing GPT categorization...")
        try:
            gpt_processor = LLMSProcessor(use_gpt=True)
            result = gpt_processor.process_file(csv_path, preview_only=True)
            
            if result['success']:
                print("✓ GPT categorization successful")
            else:
                print(f"⚠ GPT processing failed: {result['error']}")
        except Exception as e:
            print(f"⚠ GPT test failed: {e}")
    
    # Test file generation
    print("\n7. Testing file generation...")
    result = processor.process_file(csv_path, custom_filename="test_output")
    
    if result['success']:
        print("✓ File generation successful")
        print(f"  - TXT: {result['files']['txt_path']}")
        print(f"  - JSON: {result['files']['json_path']}")
        
        # Show preview of generated file
        with open(result['files']['txt_path'], 'r') as f:
            content = f.read()
            lines = content.split('\n')[:20]
            print("\n--- Output Preview ---")
            print('\n'.join(lines))
            if len(content.split('\n')) > 20:
                print("...")
    else:
        print(f"✗ File generation failed: {result['error']}")
        return False
    
    print("\n✓ All tests passed! Your setup is working correctly.")
    print("\nNext steps:")
    print("1. Try with your own Screaming Frog CSV: python run.py your-file.csv")
    print("2. Use --use-gpt flag for AI categorization")
    print("3. Run 'streamlit run app.py' when we build the UI")
    
    return True

if __name__ == "__main__":
    test_backend()