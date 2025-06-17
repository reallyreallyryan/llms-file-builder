# main.py

import os
import pandas as pd
from collections import defaultdict
from gpt_builder import build_llms_with_gpt

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")

def classify_section(url: str, title: str = "", description: str = "") -> str:
    """Smarter classification based on URL, title, and description."""
    text = f"{url} {title} {description}".lower()

    if any(x in text for x in ["provider", "pa-c", "-md", "physiatrist"]):
        return "Medical Providers"
    if any(x in text for x in ["prp", "injection", "treatment", "therapy", "bmac", "prolotherapy"]):
        return "Services"
    if any(x in text for x in ["knee", "back", "neck", "hip", "shoulder", "sciatica", "pain", "arthritis"]):
        return "Areas Treated"
    if any(x in text for x in ["blog", "guide", "understanding", "explained", "how to", "tips", "faq", "insights"]):
        return "Blogs"
    if any(x in text for x in ["about", "contact", "locations", "appointment", "insurance", "privacy policy"]):
        return "General Info"

    return "Other"

def parse_csv(csv_path):
    df = pd.read_csv(csv_path)

    if df.empty:
        raise ValueError("CSV file is empty.")

    homepage_row = df.iloc[0]
    homepage = {
        "url": str(homepage_row["Address"]).strip(),
        "title": str(homepage_row["Title 1"]).strip(),
        "description": str(homepage_row["Meta Description 1"]).strip()
    }

    pages = []
    for _, row in df.iloc[1:].iterrows():
        url = str(row.get("Address", "")).strip()
        title = str(row.get("Title 1", "")).strip()
        meta = str(row.get("Meta Description 1", "")).strip()
        status = str(row.get("Status Code", "")).strip()
        indexable = str(row.get("Indexability", "")).strip()

        if not url or status != "200" or indexable.lower() != "indexable":
            continue

        description = meta or title or "No description available."
        pages.append({
            "url": url,
            "title": title,
            "description": description
        })

    return homepage, pages

def group_and_write_manually(homepage, pages, output_filename="LLMS.txt"):
    sections = defaultdict(list)

    for page in pages:
        section = classify_section(page["url"], page["title"], page["description"])
        sections[section].append(page)

    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

    path = os.path.join(EXPORT_DIR, output_filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {homepage.get('title', 'Website')}\n\n")
        f.write(f"{homepage.get('description', 'No description.')}\n\n")

        for section, items in sections.items():
            f.write(f"## {section}\n")
            for page in items:
                title = page["title"] or page["url"]
                desc = page["description"]
                f.write(f"- [{title}]({page['url']}): {desc}\n")
            f.write("\n")

    return path

def run_tool(input_data: dict) -> dict:
    csv_path = input_data.get("csv_path")
    use_gpt = input_data.get("use_gpt", False)

    if not csv_path or not os.path.exists(csv_path):
        return {"success": False, "error": "Missing or invalid CSV path."}

    try:
        homepage, pages = parse_csv(csv_path)

        if use_gpt:
            content = build_llms_with_gpt(
                site_title=homepage["title"],
                homepage_desc=homepage["description"],
                pages=pages
            )

            if not os.path.exists(EXPORT_DIR):
                os.makedirs(EXPORT_DIR)
            gpt_path = os.path.join(EXPORT_DIR, "LLMS.txt")
            with open(gpt_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "success": True,
                "file": gpt_path,
                "generated_by": "gpt",
                "total_pages": len(pages)
            }

        else:
            manual_path = group_and_write_manually(homepage, pages)
            return {
                "success": True,
                "file": manual_path,
                "generated_by": "manual",
                "total_pages": len(pages)
            }

    except Exception as e:
        return {"success": False, "error": str(e)}
