# enhance_descriptions.py
"""
Post-process LLMS.txt to enhance descriptions with GPT
Keeps your accurate categorization, just improves descriptions
"""
import json
import re
from openai import OpenAI
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

def enhance_descriptions(json_path: str, sections_to_enhance: list = None):
    """
    Enhance descriptions for specific sections using GPT-3.5
    
    Args:
        json_path: Path to the LLMS.json file
        sections_to_enhance: List of sections to enhance (default: Services, Providers)
    """
    
    # Load the JSON file
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Default to enhancing high-value sections
    if sections_to_enhance is None:
        sections_to_enhance = ["Services", "Providers"]
    
    enhanced_data = data.copy()
    
    for section_name in sections_to_enhance:
        if section_name not in data['sections']:
            continue
            
        pages = data['sections'][section_name]
        
        # Process in small batches of 10 pages
        for i in range(0, len(pages), 10):
            batch = pages[i:i+10]
            
            # Simple prompt focused ONLY on descriptions
            prompt = f"""
Write compelling descriptions for AI search engines (ChatGPT, Claude, Perplexity) for these {section_name} pages.
Each description should be 15-20 words, highlighting the key benefit or solution.


Pages:
"""
            for page in batch:
                prompt += f"\nURL: {page['url']}\nTitle: {page['title']}\n"
            
            prompt += """
Return JSON array with url and enhanced description only:
[{"url": "...", "description": "..."}, ...]
"""
            
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=500
                )
                
                content = response.choices[0].message.content
                # Extract JSON
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    enhancements = json.loads(json_match.group())
                    
                    # Update descriptions
                    for enhancement in enhancements:
                        for j, page in enumerate(batch):
                            if page['url'] == enhancement['url']:
                                enhanced_data['sections'][section_name][i+j]['description'] = enhancement['description']
                                break
                
                print(f"Enhanced {len(batch)} {section_name} descriptions")
                
            except Exception as e:
                print(f"Error enhancing batch: {e}")
                # Keep original descriptions on error
    
    return enhanced_data

def regenerate_txt_from_json(enhanced_data: dict, output_path: str):
    """Regenerate LLMS.txt from enhanced JSON data"""
    lines = []
    
    # Header
    metadata = enhanced_data['metadata']
    lines.append(f"# {metadata['site_title']}")
    lines.append("")
    lines.append(f"> {metadata['site_summary']}")
    lines.append("")
    
    # Sections
    for section, pages in enhanced_data['sections'].items():
        if not pages:
            continue
            
        lines.append(f"## {section}")
        lines.append("")
        
        for page in pages:
            url = page['url']
            title = page['title']
            description = page.get('description', '')
            
            if description:
                lines.append(f"- [{title}]({url}): {description}")
            else:
                lines.append(f"- [{title}]({url})")
        
        lines.append("")
    
    # Save
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"Enhanced LLMS.txt saved to: {output_path}")

# Usage example
if __name__ == "__main__":
    # First, generate with pattern-based (accurate categorization)
    # python run_simple.py data.csv --output accurate_categories
    
    # Then enhance descriptions
    json_path = "exports/accurate_categories.json"
    enhanced_data = enhance_descriptions(json_path, sections_to_enhance=["Services", "Providers"])
    
    # Save enhanced version
    regenerate_txt_from_json(enhanced_data, "exports/accurate_categories_enhanced.txt")