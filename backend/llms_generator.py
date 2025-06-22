# backend/llms_generator.py
"""
Generates LLMS.txt files following the specification
"""
import os
import json
import logging
import re
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMSGenerator:
    """Generate LLMS.txt files from categorized data"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    CATEGORY_ORDER = [
        "About",           # Site context first
        "Services",        # Core offerings
        "Providers",       # Who performs services
        "Locations",       # Where to get services
        "Patient Resources", # Supporting info
        "Blog"             # Educational content last
    ]
    
    def generate_markdown(self, 
                         site_metadata: Dict,
                         categorized_pages: Dict[str, List[Dict]],
                         include_stats: bool = True) -> str:
        """Generate the LLMS.txt markdown content"""
        lines = []
        
        # Header
        lines.append(f"# {site_metadata.get('site_title', 'Website')}")
        lines.append("")
        
        # Site summary
        if site_metadata.get('site_summary'):
            lines.append(f"> {site_metadata['site_summary']}")
            lines.append("")
        
        # Optional metadata comment
        if include_stats:
            lines.append(f"<!-- Generated on {datetime.now().strftime('%Y-%m-%d')} -->")
            total_pages = sum(len(pages) for pages in categorized_pages.values())
            lines.append(f"<!-- Total pages: {total_pages} -->")
            lines.append("")
        
        # Categories and pages
        for category, pages in categorized_pages.items():
            if not pages:  # Skip empty categories
                continue
                
            lines.append(f"## {category}")
            lines.append("")
            
            # Sort pages by title for consistency
            sorted_pages = sorted(pages, key=lambda x: x.get('title', ''))
            
            for page in sorted_pages:
                url = page.get('url', '')
                title = page.get('title', 'Untitled')
                description = page.get('description', '')
                
                # Format the line
                if description:
                    lines.append(f"- [{title}]({url}): {description}")
                else:
                    lines.append(f"- [{title}]({url})")
            
            lines.append("")  # Empty line after each section
        
        for category, pages in categorized_pages.items():
            if category not in self.CATEGORY_ORDER and pages:
                lines.append(f"## {category}")
                lines.append("")
                
                sorted_pages = sorted(pages, key=lambda x: x.get('title', ''))
                
                for page in sorted_pages:
                    url = page.get('url', '')
                    title = page.get('title', 'Untitled')
                    description = page.get('description', '')
                    
                    if description:
                        lines.append(f"- [{title}]({url}): {description}")
                    else:
                        lines.append(f"- [{title}]({url})")
                
                lines.append("")
        
        for category, pages in categorized_pages.items():
            if category not in self.CATEGORY_ORDER and pages:
                lines.append(f"## {category}")
                lines.append("")
                
                sorted_pages = sorted(pages, key=lambda x: x.get('title', ''))
                
                for page in sorted_pages:
                    url = page.get('url', '')
                    title = page.get('title', 'Untitled')
                    description = page.get('description', '')
                    
                    if description:
                        lines.append(f"- [{title}]({url}): {description}")
                    else:
                        lines.append(f"- [{title}]({url})")
                
                lines.append("")
        
        return '\n'.join(lines)
    
    def generate_json(self,
                     site_metadata: Dict,
                     categorized_pages: Dict[str, List[Dict]],
                     stats: Optional[Dict] = None) -> Dict:
        """Generate JSON version of the LLMS data"""
        # Convert any numpy/pandas types to Python native types
        def convert_to_serializable(obj):
            """Convert numpy/pandas types to Python native types"""
            try:
                import numpy as np
                import pandas as pd
                
                if isinstance(obj, (np.integer, np.int64)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, pd.Series):
                    return obj.tolist()
            except ImportError:
                pass
            
            # Handle regular Python types
            if hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            else:
                return obj
        
        # Clean stats to ensure JSON serializable
        clean_stats = convert_to_serializable(stats) if stats else {}
        
        return {
            "metadata": {
                "site_title": site_metadata.get('site_title', ''),
                "site_summary": site_metadata.get('site_summary', ''),
                "site_url": site_metadata.get('site_url', ''),
                "generated_at": datetime.now().isoformat(),
                "version": "1.0"
            },
            "sections": categorized_pages,
            "stats": clean_stats
        }
    
    def validate_output(self, content: str) -> List[str]:
        """Validate the generated LLMS.txt content"""
        issues = []
        lines = content.split('\n')
        
        # Check for required elements
        if not any(line.startswith('# ') for line in lines):
            issues.append("Missing H1 header (site title)")
        
        if not any(line.startswith('## ') for line in lines):
            issues.append("No sections found (H2 headers)")
        
        # Check for malformed links - improved regex
        link_count = 0
        link_pattern = re.compile(r'^- \[([^\]]+)\]\(([^)]+)\)')
        
        for line in lines:
            if line.strip().startswith('- ['):
                link_count += 1
                # Check if it's a valid markdown link format
                if not link_pattern.match(line.strip()):
                    # Only flag as malformed if it truly doesn't match the pattern
                    if '](' not in line:
                        issues.append(f"Malformed link (missing ']('): {line[:50]}...")
        
        if link_count == 0:
            issues.append("No links found in output")
        
        # Check for reasonable length
        if len(content) < 100:
            issues.append("Output seems too short")
        
        return issues
    
    def save_files(self,
                  site_metadata: Dict,
                  categorized_pages: Dict[str, List[Dict]],
                  stats: Optional[Dict] = None,
                  filename_prefix: str = "LLMS") -> Dict[str, str]:
        """Save both LLMS.txt and LLMS.json files"""
        # Generate content
        markdown_content = self.generate_markdown(site_metadata, categorized_pages)
        json_content = self.generate_json(site_metadata, categorized_pages, stats)
        
        # Validate markdown
        issues = self.validate_output(markdown_content)
        if issues:
            logger.warning(f"Validation issues found: {', '.join(issues)}")
        
        # Save files
        txt_path = os.path.join(self.output_dir, f"{filename_prefix}.txt")
        json_path = os.path.join(self.output_dir, f"{filename_prefix}.json")
        
        # Write markdown
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Write JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Files saved: {txt_path}, {json_path}")
        
        return {
            'txt_path': txt_path,
            'json_path': json_path,
            'validation_issues': issues
        }
    
    def preview(self, 
               site_metadata: Dict,
               categorized_pages: Dict[str, List[Dict]],
               max_lines: int = 50) -> str:
        """Generate a preview of the LLMS.txt content"""
        full_content = self.generate_markdown(site_metadata, categorized_pages, include_stats=False)
        lines = full_content.split('\n')
        
        if len(lines) <= max_lines:
            return full_content
        
        # Truncate and add indicator
        preview_lines = lines[:max_lines]
        preview_lines.append("...")
        preview_lines.append(f"[{len(lines) - max_lines} more lines]")
        
        return '\n'.join(preview_lines)