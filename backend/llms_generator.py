
"""
Generates LLMS.txt files following the specification
OPTIMIZED for healthcare marketing sites
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

    # Optimized category order for healthcare marketing sites
    CATEGORY_ORDER = [
        "About",           # Site context first
        "Services",        # Core offerings - most important for healthcare
        "Providers",       # Who performs services
        "Areas Treated",   # What conditions are treated
        "Locations",       # Where to get services
        "Before & After",  # Visual proof/results 
        "Patient Resources", # Supporting info
        "Blog"             # Educational content last
    ]
    
    def generate_markdown(self, 
                         site_metadata: Dict,
                         categorized_pages: Dict[str, List[Dict]],
                         include_stats: bool = True) -> str:
        """Generate the LLMS.txt markdown content optimized for healthcare"""
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
        
        # Categories and pages - Use healthcare-optimized order
        for category in self.CATEGORY_ORDER:
            if category in categorized_pages and categorized_pages[category]:
                pages = categorized_pages[category]
                
                lines.append(f"## {category}")
                lines.append("")
                
                # Sort pages by title for consistency, but prioritize important ones
                sorted_pages = self._sort_pages_for_category(category, pages)
                
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
        
        # Then add any categories not in CATEGORY_ORDER (like "Other")
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
    
    def _sort_pages_for_category(self, category: str, pages: List[Dict]) -> List[Dict]:
        """Sort pages within each category for optimal presentation"""
        
        if category == "Services":
            # Put main services first, then specific procedures
            def service_priority(page):
                title = page.get('title', '').lower()
                if any(term in title for term in ['breast reconstruction', 'breast surgery', 'cosmetic surgery']):
                    return 0  # Main services first
                elif any(term in title for term in ['diep', 'tram', 'implant']):
                    return 1  # Specific procedures second
                else:
                    return 2  # Everything else
            
            return sorted(pages, key=lambda x: (service_priority(x), x.get('title', '')))
        
        elif category == "Before & After":
            # Group by procedure type
            def before_after_priority(page):
                title = page.get('title', '').lower()
                if 'breast reconstruction' in title:
                    return 0
                elif 'breast' in title:
                    return 1
                elif any(term in title for term in ['diep', 'flap']):
                    return 2
                else:
                    return 3
            
            return sorted(pages, key=lambda x: (before_after_priority(x), x.get('title', '')))
        
        elif category == "Blog":
            # Put recent achievements and milestones first
            def blog_priority(page):
                title = page.get('title', '').lower()
                if any(term in title for term in ['milestone', 'achievement', 'record', 'years of']):
                    return 0  # Achievements first
                elif any(term in title for term in ['news', 'announcement', 'featured']):
                    return 1  # News second
                else:
                    return 2  # Regular blog content
            
            return sorted(pages, key=lambda x: (blog_priority(x), x.get('title', '')))
        
        else:
            # Default alphabetical sort for other categories
            return sorted(pages, key=lambda x: x.get('title', ''))
    
    def validate_output(self, content: str) -> List[str]:
        """Validate the generated LLMS.txt content with healthcare-specific checks"""
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
        
        # Healthcare-specific validations
        services_found = any('## Services' in line for line in lines)
        if not services_found:
            issues.append("No Services section found - critical for healthcare sites")
        
        # Check for reasonable length
        if len(content) < 100:
            issues.append("Output seems too short")
        
        return issues
    
    def save_files(self,
                  site_metadata: Dict,
                  categorized_pages: Dict[str, List[Dict]],
                  stats: Optional[Dict] = None,
                  filename_prefix: str = "LLMS") -> Dict[str, str]:
        """Save LLMS.txt file optimized for AI search engines"""
        # Generate content
        markdown_content = self.generate_markdown(site_metadata, categorized_pages)
        
        # Validate markdown
        issues = self.validate_output(markdown_content)
        if issues:
            logger.warning(f"Validation issues found: {', '.join(issues)}")
        
        # Save file
        txt_path = os.path.join(self.output_dir, f"{filename_prefix}.txt")
        
        # Write markdown
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"LLMS.txt file saved: {txt_path}")
        
        return {
            'txt_path': txt_path,
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