import json
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    tokens_per_message = 3
    tokens_per_name = 1
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens

def build_llms_with_gpt(pages: list, site_name: str, summary: str, chunk_size: int = 60):
    if not pages:
        return {"success": False, "error": "No pages to process."}

    all_chunks = [pages[i:i + chunk_size] for i in range(0, len(pages), chunk_size)]
    print(f"Sending {len(all_chunks)} GPT batches...")

    section_data = {}

    for i, chunk in enumerate(all_chunks):
        print(f"Processing chunk {i + 1} of {len(all_chunks)}...")
        simplified = [
            {
                "title": p.get("Title", ""),
                "url": p.get("Address", ""),
                "meta": p.get("Meta Description", "")
            }
            for p in chunk
        ]

        prompt = f"""
You are helping organize web pages for AI search.

Group the following pages into sections. Use these standard ones when applicable:
- Services
- Areas Treated
- Providers
- Locations
- Blog

Write 1-2 sentence descriptions for each URL that help AI search understand what the page offers. 

Only use the info in the title, meta, or url. If unsure, group under "Other".

Respond in JSON with section names as keys.

Input:
{json.dumps(simplified)}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.choices[0].message.content
            gpt_sections = json.loads(content)

            for section, pages in gpt_sections.items():
                if section not in section_data:
                    section_data[section] = []
                section_data[section].extend(pages)

        except Exception as e:
            return {"success": False, "error": str(e)}

    return {
        "success": True,
        "site_title": site_name,
        "site_summary": summary,
        "sections": section_data
    }
