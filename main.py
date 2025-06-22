import pandas as pd
import os
import json

EXPORTS_DIR = "exports"

SECTION_PATTERNS = {
    "Services": ["services", "therapy", "injection", "prp", "bmac", "treatment", "decompression"],
    "Areas Treated": ["areas-we-treat", "pain", "sciatica", "shoulder", "hip", "back", "neck"],
    "Blogs": ["blog", "articles", "education", "/news", "/resources"],
    "Medical Providers": ["physician", "provider", "doctor", "team", "pa-c", "md", "do"],
    "Locations": ["locations", "contact", "scottsdale", "mesa", "phoenix", "gilbert"],
    "Patient Resources": ["forms", "insurance", "download", "privacy", "appointment", "faq"],
    "About Us": ["about", "mission", "careers", "values"]
}


def normalize_url(url):
    return url.rstrip("/").strip()

def deduplicate_pages(pages):
    seen = set()
    deduped = []
    for page in pages:
        url = normalize_url(page.get("Address", ""))
        if url not in seen:
            seen.add(url)
            deduped.append(page)
    return deduped

def parse_site_metadata(df):
    homepage = df.iloc[0]
    site_title = homepage.get("Title 1", "Website")
    site_summary = homepage.get("Meta Description 1", "")
    return site_title.strip(), site_summary.strip()

def classify_section(url, title):
    url_lower = url.lower()
    title_lower = title.lower()
    for section, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if pattern in url_lower or pattern in title_lower:
                return section
    return "Other"

def run_tool(input_data: dict) -> dict:
    csv_path = input_data.get("csv_path")

    if not csv_path or not os.path.exists(csv_path):
        return {"success": False, "error": "CSV path is missing or invalid."}

    df = pd.read_csv(csv_path)
    df = df[df["Status Code"] == 200]
    df = df[df["Indexability"] == "Indexable"]
    df = df.fillna("")

    site_title, site_summary = parse_site_metadata(df)
    pages = deduplicate_pages(df.to_dict(orient="records"))

    grouped = {}
    seen_urls = set()
    for page in pages:
        url = normalize_url(page.get("Address", ""))
        if url in seen_urls:
            continue
        seen_urls.add(url)
        title = page.get("Title 1", "Untitled").strip()
        desc = page.get("Meta Description 1", "").strip()
        section = classify_section(url, title)
        grouped.setdefault(section, []).append({
            "url": url,
            "title": title,
            "description": desc
        })

    txt_lines = [f"# {site_title}", "", site_summary, ""]
    for section, section_pages in grouped.items():
        txt_lines.append(f"## {section}\n")
        for page in section_pages:
            txt_lines.append(f"- [{page['title']}]({page['url']}): {page['description']}")
        txt_lines.append("")

    os.makedirs(EXPORTS_DIR, exist_ok=True)
    txt_path = os.path.join(EXPORTS_DIR, "LLMS.txt")
    json_path = os.path.join(EXPORTS_DIR, "LLMS.json")

    with open(txt_path, "w") as f:
        f.write("\n".join(txt_lines))

    with open(json_path, "w") as f:
        json.dump(grouped, f, indent=2)

    return {
        "success": True,
        "file": txt_path,
        "json": json_path,
        "section_count": len(grouped),
        "total_pages": len(seen_urls)
    }
