# backend/categorizer.py
"""
Handles page categorization using pattern matching and AI
"""
import re
import json
import logging
from typing import Dict, List, Optional
from collections import defaultdict
import tiktoken
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class Categorizer:
    """Categorize pages using patterns or GPT"""
    
    # Default section patterns for pattern-based categorization
    DEFAULT_PATTERNS = {
        "Services": [
            "services", "therapy", "treatment", "procedure", "injection", 
            "prp", "bmac", "decompression", "ablation", "stimulation",
            "surgery", "surgical", "operation", "removal", "repair"
        ],
        "Areas Treated": [
            "areas-we-treat", "conditions", "pain", "sciatica", "shoulder", 
            "hip", "back", "neck", "knee", "ankle", "elbow", "spine",
            "joint", "muscle", "tendon", "ligament"
        ],
        "Blog": [
            "blog", "article", "post", "news", "education", "learn",
            "guide", "tips", "advice", "resource", "insights", "update"
        ],
        "Providers": [
            "physician", "provider", "doctor", "team", "staff",
            "pa-c", "md", "do", "phd", "nurse", "therapist",
            "surgeon", "specialist", "expert"
        ],
        "Locations": [
            "location", "office", "clinic", "contact", "directions",
            "address", "map", "hours", "parking", "facility"
        ],
        "Patient Resources": [
            "patient", "form", "insurance", "download", "faq",
            "appointment", "schedule", "privacy", "policy", "rights",
            "billing", "payment", "testimonial", "review"
        ],
        "About": [
            "about", "mission", "vision", "values", "history",
            "career", "join", "team", "culture", "story",
            "welcome", "introduction", "who-we-are"
        ]
    }
    
    def __init__(self, use_gpt: bool = False, api_key: Optional[str] = None):
        self.use_gpt = use_gpt
        self.patterns = self.DEFAULT_PATTERNS.copy()
        
        if use_gpt:
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required for GPT categorization")
            
            self.client = OpenAI(api_key=api_key)
            self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    def update_patterns(self, custom_patterns: Dict[str, List[str]]):
        """Update or add custom categorization patterns"""
        self.patterns.update(custom_patterns)
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        return url.rstrip("/").strip().lower()
    
    def extract_url_segments(self, url: str) -> List[str]:
        """Extract meaningful segments from URL"""
        # Remove protocol and domain
        path = re.sub(r'^https?://[^/]+', '', url)
        # Split by / and - and _
        segments = re.split(r'[/\-_]', path)
        # Filter out empty strings and common words
        return [s for s in segments if s and len(s) > 2]
    
    def extract_title_from_url(self, url: str) -> str:
        """Extract a meaningful title from URL when page title is empty"""
        # Remove protocol and domain
        path = re.sub(r'^https?://[^/]+/', '', url)
        
        # Remove query parameters and fragments
        path = re.sub(r'[?#].*$', '', path)
        
        # Remove file extension
        path = re.sub(r'\.[^/]+$', '', path)
        
        # Handle special cases
        if not path or path == '/':
            return 'Homepage'
        
        # Split by / and take the last meaningful segment
        segments = [s for s in path.split('/') if s]
        
        if segments:
            # Take the last segment or last two if more descriptive
            if len(segments) >= 2 and len(segments[-1]) < 20:
                # Combine last two segments for better context
                title_parts = segments[-2:]
            else:
                title_parts = [segments[-1]]
            
            # Convert to readable title
            title = ' '.join(title_parts)
            # Replace hyphens/underscores with spaces
            title = title.replace('-', ' ').replace('_', ' ')
            # Title case
            title = title.title()
            
            return title
        
        return 'Page'
    
    def prepare_page_for_display(self, page: Dict) -> Dict:
        """Prepare page data with proper title handling"""
        title = page.get('Title 1', '').strip()
        
        # If title is empty, try to extract from URL
        if not title:
            url = page.get('Address', '')
            title = self.extract_title_from_url(url)
        
        # Get description, fallback to H1 or generate from URL
        description = page.get('Meta Description 1', '').strip()
        if not description:
            h1 = page.get('H1-1', '').strip()
            if h1:
                description = h1
            else:
                # Generate description from title
                description = f"Information about {title.lower()}"
        
        return {
            'url': page.get('Address', ''),
            'title': title,
            'description': description
        }
    
    def pattern_based_categorize(self, page: Dict) -> str:
        """Categorize a single page using patterns"""
        url = self.normalize_url(page.get('Address', ''))
        title = page.get('Title 1', '').lower()
        meta = page.get('Meta Description 1', '').lower()
        h1 = page.get('H1-1', '').lower()
        
        # Combine all text for matching
        combined_text = f"{url} {title} {meta} {h1}"
        url_segments = self.extract_url_segments(url)
        
        # Score each category
        category_scores = defaultdict(int)
        
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                # Check in combined text
                if pattern_lower in combined_text:
                    category_scores[category] += 2
                # Check in URL segments (higher weight)
                for segment in url_segments:
                    if pattern_lower in segment:
                        category_scores[category] += 3
        
        # Return category with highest score, or "Other"
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        return "Other"
    
    def prepare_page_for_gpt(self, page: Dict) -> Dict:
        """Prepare page data for GPT processing"""
        # First prepare display version to get proper title
        display_data = self.prepare_page_for_display(page)
        
        return {
            "url": display_data['url'],
            "title": display_data['title'][:100],  # Limit length
            "meta": display_data['description'][:150],
            "h1": page.get("H1-1", "")[:100]
        }
    
    def estimate_tokens(self, pages: List[Dict]) -> int:
        """Estimate token count for GPT request"""
        simplified = [self.prepare_page_for_gpt(p) for p in pages]
        content = json.dumps(simplified)
        return len(self.encoding.encode(content))
    
    def gpt_categorize_batch(self, pages: List[Dict], site_context: str = "") -> Dict[str, List[Dict]]:
        """Categorize a batch of pages using GPT"""
        simplified = [self.prepare_page_for_gpt(p) for p in pages]
        
        # Get available categories
        categories = list(self.patterns.keys()) + ["Other"]
        
        prompt = f"""You are helping organize website pages for an LLMS.txt file.

{f"Site context: {site_context}" if site_context else ""}

Group these pages into logical sections. Use these categories when applicable:
{', '.join(categories)}

For each page, write a 1-2 sentence description that explains what the page offers, 
based ONLY on the URL, title, meta description, and H1 provided.

Important:
- If a URL looks like an image or asset file (ends in .jpg, .png, .css, .js, etc), skip it
- Focus on actual content pages
- Use the title provided, don't change it

Return JSON with section names as keys and arrays of objects with 'url', 'title', and 'description'.

Pages to categorize:
{json.dumps(simplified, indent=2)}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                
                # Map URLs back to original page data
                url_to_page = {p['Address']: p for p in pages}
                
                # Update with original titles if they exist
                for category, items in result.items():
                    for item in items:
                        original_page = url_to_page.get(item['url'])
                        if original_page:
                            display_data = self.prepare_page_for_display(original_page)
                            item['title'] = display_data['title']
                            if not item.get('description'):
                                item['description'] = display_data['description']
                
                return result
            else:
                raise ValueError("No valid JSON in GPT response")
                
        except Exception as e:
            logger.error(f"GPT categorization failed: {str(e)}")
            raise
    
    def categorize_pages(self, pages: List[Dict], site_metadata: Dict) -> Dict[str, List[Dict]]:
        """Main categorization method"""
        if self.use_gpt:
            return self._gpt_categorize_all(pages, site_metadata)
        else:
            return self._pattern_categorize_all(pages)
    
    def _pattern_categorize_all(self, pages: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize all pages using patterns"""
        categorized = defaultdict(list)
        
        for page in pages:
            category = self.pattern_based_categorize(page)
            
            # Prepare page entry with proper display data
            page_entry = self.prepare_page_for_display(page)
            
            categorized[category].append(page_entry)
        
        # Sort categories by number of pages (descending)
        sorted_categories = dict(
            sorted(categorized.items(), 
                   key=lambda x: len(x[1]), 
                   reverse=True)
        )
        
        return sorted_categories
    
    def _gpt_categorize_all(self, pages: List[Dict], site_metadata: Dict) -> Dict[str, List[Dict]]:
        """Categorize all pages using GPT in chunks"""
        MAX_TOKENS_PER_REQUEST = 3000  # Leave room for response
        categorized = defaultdict(list)
        
        # Create site context
        site_context = f"{site_metadata.get('site_title', '')} - {site_metadata.get('site_summary', '')}"
        
        # Process in chunks
        current_chunk = []
        current_tokens = 0
        
        logger.info(f"Processing {len(pages)} pages with GPT...")
        
        for i, page in enumerate(pages):
            page_tokens = self.estimate_tokens([page])
            
            if current_tokens + page_tokens > MAX_TOKENS_PER_REQUEST and current_chunk:
                # Process current chunk
                try:
                    chunk_results = self.gpt_categorize_batch(current_chunk, site_context)
                    for category, items in chunk_results.items():
                        categorized[category].extend(items)
                    logger.info(f"Processed chunk: {len(current_chunk)} pages")
                except Exception as e:
                    logger.error(f"GPT chunk failed, falling back to patterns: {e}")
                    # Fallback to pattern-based for this chunk
                    for p in current_chunk:
                        category = self.pattern_based_categorize(p)
                        page_entry = self.prepare_page_for_display(p)
                        categorized[category].append(page_entry)
                
                # Reset chunk
                current_chunk = []
                current_tokens = 0
            
            current_chunk.append(page)
            current_tokens += page_tokens
            
            # Progress logging
            if (i + 1) % 50 == 0:
                logger.info(f"Progress: {i + 1}/{len(pages)} pages")
        
        # Process final chunk
        if current_chunk:
            try:
                chunk_results = self.gpt_categorize_batch(current_chunk, site_context)
                for category, items in chunk_results.items():
                    categorized[category].extend(items)
            except Exception as e:
                logger.error(f"Final GPT chunk failed: {e}")
                # Fallback for final chunk
                for p in current_chunk:
                    category = self.pattern_based_categorize(p)
                    page_entry = self.prepare_page_for_display(p)
                    categorized[category].append(page_entry)
        
        return dict(categorized)