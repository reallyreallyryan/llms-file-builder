# LLMS File Builder 🧠📄

Turn your Screaming Frog SEO crawl into a GPT-enhanced LLMS.txt file — grouped, summarized, and markdown-formatted for internal use or AI training.

---

## 🚀 Features

- ✅ Filters to indexable, 200-status pages
- 🤖 Uses `gpt-3.5-turbo` to intelligently group and describe pages
- 🗂 Outputs a clean, structured `LLMS.txt` file with sections
- ⚡ Handles large sites using chunked GPT calls

---

## 🛠 Setup

1. Clone the repo and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

2. Create a .env file with your OpenAI key:

OPENAI_API_KEY=sk-your-key-here


📂 Usage
Export a full Internal HTML crawl from Screaming Frog.

Then run:
python run.py --csv_path="data/your_export.csv" --use_gpt

The output file will be saved to:
exports/LLMS.txt

🧠 Example Output
# My Medical Site

We specialize in non-surgical treatment for joint pain and sports injuries.

## Services
- [PRP Therapy](...): Platelet-rich plasma treatments for tendon pain.
- [Kyphoplasty](...): Minimally invasive procedure to treat spinal fractures.

## Areas Treated
- [Hip Pain](...): Diagnosis and regenerative therapies for chronic hip issues.

