# gpt_builder.py (Chunked GPT Processing)

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from math import ceil

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHUNK_SIZE = 50  # safe number for GPT-4 token limits

def _build_prompt(site_title, homepage_desc, pages_chunk):
    return {
        "site": {
            "title": site_title,
            "homepage_description": homepage_desc
        },
        "pages": pages_chunk
    }

def _send_chunk_to_gpt(prompt_data):
    system_prompt = (
        "You are a skilled SEO assistant.\n"
        "You will receive a website title, description, and a list of pages with URLs and short descriptions.\n"
        "Group the pages into smart, relevant categories (e.g., Services, Areas Treated, Providers, Blogs, General Info).\n"
        "Return only the markdown-formatted LLMS sections for these pages.\n"
        "Do not repeat the site title or homepage summary."
    )

    user_prompt = f"Generate LLMS-style markdown for this chunk:\n{json.dumps(prompt_data, indent=2)}"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()

def build_llms_with_gpt(site_title, homepage_desc, pages):
    all_chunks = [pages[i:i + CHUNK_SIZE] for i in range(0, len(pages), CHUNK_SIZE)]
    print(f"Sending {len(all_chunks)} GPT batches...")

    llms_sections = []

    for i, chunk in enumerate(all_chunks):
        prompt = _build_prompt(site_title, homepage_desc, chunk)
        print(f"Processing chunk {i + 1} of {len(all_chunks)}...")
        section_md = _send_chunk_to_gpt(prompt)
        llms_sections.append(section_md)

    # Final combined markdown
    full_output = f"# {site_title}\n\n{homepage_desc}\n\n" + "\n\n".join(llms_sections)
    return full_output
