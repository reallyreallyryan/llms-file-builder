# backend/llms_processor.py
"""
Main processing orchestrator for LLMS File Builder
"""
import logging
from typing import Dict, Optional
from pathlib import Path

from .csv_processor import CSVProcessor
from .categorizer import Categorizer
from .llms_generator import LLMSGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMSProcessor:
    """Main orchestrator for LLMS file generation"""
    
    def __init__(self, 
                 output_dir: str = "exports",
                 use_gpt: bool = False,
                 api_key: Optional[str] = None):
        self.output_dir = output_dir
        self.use_gpt = use_gpt
        self.api_key = api_key
        
        # Initialize components
        self.csv_processor = None
        self.categorizer = Categorizer(use_gpt=use_gpt, api_key=api_key)
        self.generator = LLMSGenerator(output_dir=output_dir)
        
        # Store results for access
        self.results = {}
    
    def update_patterns(self, custom_patterns: Dict):
        """Update categorization patterns"""
        self.categorizer.update_patterns(custom_patterns)
    
    def process_file(self, 
                    csv_path: str,
                    preview_only: bool = False,
                    custom_filename: Optional[str] = None) -> Dict:
        """
        Main processing pipeline
        
        Args:
            csv_path: Path to Screaming Frog CSV
            preview_only: If True, only generate preview without saving
            custom_filename: Custom output filename (without extension)
            
        Returns:
            Dictionary with results and status
        """
        try:
            # Initialize CSV processor
            self.csv_processor = CSVProcessor(csv_path)
            
            # Process CSV
            logger.info(f"Processing CSV file: {csv_path}")
            processed_data = self.csv_processor.process()
            
            pages = processed_data['pages']
            site_metadata = processed_data['site_metadata']
            stats = processed_data['stats']
            
            logger.info(f"Found {len(pages)} indexable pages")
            
            # Categorize pages
            logger.info("Categorizing pages...")
            categorized = self.categorizer.categorize_pages(pages, site_metadata)
            
            # Log category distribution
            for category, items in categorized.items():
                logger.info(f"  {category}: {len(items)} pages")
            
            # Generate output
            if preview_only:
                preview = self.generator.preview(site_metadata, categorized)
                self.results = {
                    'success': True,
                    'preview': preview,
                    'stats': stats,
                    'categories': {k: len(v) for k, v in categorized.items()}
                }
            else:
                # Determine filename
                filename = custom_filename or Path(csv_path).stem
                
                # Save files
                save_results = self.generator.save_files(
                    site_metadata,
                    categorized,
                    stats,
                    filename_prefix=filename
                )
                
                self.results = {
                    'success': True,
                    'files': save_results,
                    'stats': stats,
                    'categories': {k: len(v) for k, v in categorized.items()},
                    'validation_issues': save_results.get('validation_issues', [])
                }
            
            return self.results
            
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            self.results = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            return self.results
    
    def get_sample_data(self, n: int = 5) -> Optional[Dict]:
        """Get sample of processed data"""
        if self.csv_processor and self.csv_processor.processed_data:
            return {
                'sample_pages': self.csv_processor.get_sample_data(n),
                'site_metadata': self.csv_processor.processed_data.get('site_metadata', {})
            }
        return None
    
    def validate_csv(self, csv_path: str) -> Dict:
        """Validate CSV file before processing"""
        try:
            processor = CSVProcessor(csv_path)
            
            # Check file
            valid, error = processor.validate_file()
            if not valid:
                return {'valid': False, 'error': error}
            
            # Load and check columns
            processor.load_csv()
            valid, missing = processor.validate_columns()
            
            if not valid:
                return {
                    'valid': False,
                    'error': f"Missing columns: {', '.join(missing)}",
                    'available_columns': list(processor.df.columns)
                }
            
            # Get info
            col_info = processor.get_column_info()
            
            return {
                'valid': True,
                'total_rows': len(processor.df),
                'columns': col_info,
                'file_size_mb': Path(csv_path).stat().st_size / (1024 * 1024)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }