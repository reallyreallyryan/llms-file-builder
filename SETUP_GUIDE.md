LLMS File Builder - Quick Reference 🚀
Installation (One Time)
bash
git clone [repo-url]
cd llms-file-builder
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
echo "OPENAI_API_KEY=sk-..." > .env  # Optional
Screaming Frog Export (Critical!)
Open Screaming Frog → Crawl your site
Click "Internal" tab
Filter → HTML ⚠️ (This is crucial!)
File → Export → Save as CSV
Generate LLMS.txt
Fast Mode (Pattern-based)
bash
python run.py data/your-site.csv
AI-Enhanced Mode
bash
python run.py data/your-site.csv --use-gpt
GUI Mode
bash
streamlit run app.py
# Open http://localhost:8501
Common Commands
bash
# Preview without saving
python run.py data/site.csv --preview

# Custom filename
python run.py data/site.csv --output mysite

# Validate CSV only
python run.py data/site.csv --validate-only

# Force processing (skip quality warnings)
python run.py data/site.csv --force
Output Files
exports/
├── LLMS.txt      # Upload to yoursite.com/llms.txt
└── LLMS.json     # For programmatic use
Troubleshooting
Problem	Solution
"Missing columns"	Re-export from "Internal" → "HTML"
"Too many images"	You didn't filter by HTML
"GPT timeout"	Try without --use-gpt first
"No API key"	Add to .env file
Category Patterns
Default categories:

Services: /services/, therapy, treatment
Areas Treated: /conditions/, pain, symptoms
Blog: /blog/, article, news
Providers: /physicians/, doctor, team
Locations: /locations/, office, clinic
Patient Resources: forms, insurance, faq
About: /about/, mission, values
Quality Indicators
✅ Good CSV: Quality score > 80, mostly HTML pages
⚠️ OK CSV: Quality score 60-80, some non-content
❌ Poor CSV: Quality score < 60, many images/assets

Need Help?
Run python test_setup.py to verify installation
Check exports/ folder for output files
Use --validate-only to check CSV quality
Add --force to process anyway
💡 Pro Tip: Always use Screaming Frog's HTML filter for best results!

