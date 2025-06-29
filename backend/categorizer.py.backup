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
            "guide", "tips", "advice", "resource", "insights", "update",
            "announcement", "opens", "featured", "q&a", "interview" 
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
            "billing", "payment", "testimonial", "review",
            "request-appointment", "payment-plan" 
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
                raise ValueError("OpenAI API key required for GPT enhancement")
            
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
        
        # Clean up truncation marks from descriptions
        if description:
            # Remove various forms of truncation marks
            description = description.replace('[…]', '').replace('[...]', '').strip()
            description = description.replace('…', '').strip()
            
            # If description ends with incomplete sentence, try to complete it
            if description and not description[-1] in '.!?':
                # Add a period if it seems like a complete thought
                if len(description.split()) > 5:  # Has enough words
                    description += '.'
        
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
        
        # PRIORITY 0: Check for news/announcement patterns FIRST
        news_indicators = [
            'new surgical center opens',
            'opens flagship',
            'featured in forbes',
            'announcement',
            'press release',
            'news:'
        ]
        
        for indicator in news_indicators:
            if indicator in title or indicator in meta:
                return "Blog"

        # PRIORITY 1: Check URL structure first for definitive categorization
        # Blog posts should ALWAYS go in Blog category
        if '/blog/' in url:
            return "Blog"
        
        # Patient info/resources pages
        if '/patient-information/' in url or '/patient-resources/' in url:
            return "Patient Resources"
        
        # Location pages
        if '/locations/' in url:
            return "Locations"
        
        # Provider/physician pages
        if '/physicians/' in url or '/providers/' in url:
            return "Providers"
        
        # Service pages
        if '/services/' in url:
            return "Services"
        
        # PRIORITY 2: If no clear URL pattern, use content matching
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
    
    def categorize_pages(self, pages: List[Dict], site_metadata: Dict) -> Dict[str, List[Dict]]:
        """Main categorization method - ALWAYS use patterns, optionally enhance"""
        
        # ALWAYS use pattern-based categorization for accuracy
        logger.info("Using pattern-based categorization...")
        categorized = self._pattern_categorize_all(pages)
        
        # If GPT is enabled, use it ONLY for description enhancement
        if self.use_gpt:
            logger.info("Enhancing descriptions with GPT...")
            categorized = self._enhance_categorized_descriptions(categorized, site_metadata)
        
        return categorized
    
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
    
    def _enhance_categorized_descriptions(self, categorized: Dict[str, List[Dict]], 
                                         site_metadata: Dict) -> Dict[str, List[Dict]]:
        """Enhance descriptions for already-categorized pages"""
        
        # Include Blog in sections to enhance
        sections_to_enhance = ['Services', 'Providers', 'Locations', 'Blog']
        enhanced_categorized = categorized.copy()
        
        for section in sections_to_enhance:
            if section not in categorized or not categorized[section]:
                continue
                
            logger.info(f"Enhancing {len(categorized[section])} {section} descriptions...")
            
            pages = categorized[section]
            enhanced_pages = []
            
            # Process in batches of 10
            for i in range(0, len(pages), 10):
                batch = pages[i:i+10]
                
                # Different prompt for Blog section
                if section == 'Blog':
                    prompt = f"""You are optimizing blog descriptions for AI search engines (ChatGPT, Claude, Perplexity).
Site: {site_metadata.get('site_title', '')}

For each blog post below, write a 15-25 word description for an llms.txt file that. Each file should:
- Clearly states what the article teaches or covers
- Uses natural, complete sentences (no truncation marks like [...])
- Helps AI understand the content's value
- Is actionable and informative

Blog posts:
"""
                else:
                    prompt = f"""You are optimizing descriptions for AI search engines (ChatGPT, Claude, Perplexity).
Site: {site_metadata.get('site_title', '')}
Section: {section}

For each page below, write a 15-25 word description for a llms.txt file. Each file should:
- States the specific service/solution
- Includes keywords AI would search for  
- Mentions the benefit or outcome
- Is specific, not generic

Pages:
"""
                
                for j, page in enumerate(batch):
                    prompt += f"\n{j+1}. {page['title']}"
                    if page.get('description'):
                        # Clean up [...] from existing descriptions before sending to GPT
                        current_desc = page['description'].replace('[…]', '').replace('[...]', '').replace('…', '').strip()
                        prompt += f"\n   Current: {current_desc[:100]}"
                
                prompt += """

Return ONLY a JSON array with descriptions:
[{"index": 1, "description": "..."}, {"index": 2, "description": "..."}, ...]

NO other text, NO trailing commas, NO truncation marks."""

                try:
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an AI search optimization expert. Write complete, natural descriptions without truncation marks."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=600
                    )
                    
                    content = response.choices[0].message.content.strip()
                    
                    # Extract JSON more carefully
                    # Remove any markdown formatting
                    content = content.replace('```json', '').replace('```', '')
                    
                    # Find the JSON array
                    start = content.find('[')
                    end = content.rfind(']') + 1
                    
                    if start != -1 and end > start:
                        json_str = content[start:end]
                        
                        # Clean common issues
                        json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas
                        json_str = re.sub(r',\s*}', '}', json_str)
                        
                        improvements = json.loads(json_str)
                        
                        # Create enhanced batch
                        enhanced_batch = batch.copy()
                        for item in improvements:
                            idx = item.get('index', 0) - 1
                            if 0 <= idx < len(enhanced_batch) and 'description' in item:
                                enhanced_batch[idx] = batch[idx].copy()
                                enhanced_batch[idx]['description'] = item['description']
                        
                        enhanced_pages.extend(enhanced_batch)
                        logger.info(f"✓ Enhanced {len(improvements)} descriptions")
                    else:
                        # If parsing fails, keep originals
                        enhanced_pages.extend(batch)
                        logger.warning("Could not parse GPT response, keeping original descriptions")
                        
                except Exception as e:
                    logger.warning(f"Enhancement failed for batch: {e}")
                    enhanced_pages.extend(batch)  # Keep originals on error
            
            # Update the section with enhanced pages
            enhanced_categorized[section] = enhanced_pages
        
        return enhanced_categorized
    
    # DEPRECATED METHODS - Left for reference but not used
    def prepare_page_for_gpt(self, page: Dict) -> Dict:
        """DEPRECATED - Only used in old GPT categorization"""
        display_data = self.prepare_page_for_display(page)
        return {
            "url": display_data['url'],
            "title": display_data['title'][:100],
            "meta": display_data['description'][:150],
            "h1": page.get("H1-1", "")[:100]
        }
    
    def estimate_tokens(self, pages: List[Dict]) -> int:
        """DEPRECATED - Only used in old GPT categorization"""
        simplified = [self.prepare_page_for_gpt(p) for p in pages]
        content = json.dumps(simplified)
        return len(self.encoding.encode(content))
    
    def gpt_categorize_batch(self, pages: List[Dict], site_context: str = "") -> Dict[str, List[Dict]]:
        """DEPRECATED - Don't use GPT for categorization"""
        logger.warning("gpt_categorize_batch is deprecated. Use pattern-based categorization instead.")
        # Fallback to pattern-based
        fallback_results = defaultdict(list)
        for page in pages:
            category = self.pattern_based_categorize(page)
            page_entry = self.prepare_page_for_display(page)
            fallback_results[category].append(page_entry)
        return dict(fallback_results)
    
    def _gpt_categorize_all(self, pages: List[Dict], site_metadata: Dict) -> Dict[str, List[Dict]]:
        """DEPRECATED - Don't use GPT for categorization"""
        logger.warning("GPT categorization is deprecated. Using pattern-based categorization instead.")
        return self._pattern_categorize_all(pages)