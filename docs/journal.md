# LLMS.txt File Builder

This tool parses a Screaming Frog CSV export and builds a valid LLMS.txt file used for SEO upload processes.

## Input
- CSV path from Screaming Frog export
- Must include `Address` and `Status Code` columns

## Output
- `LLMS.txt` file with only indexable (200 status) URLs
- Saved in `/exports/`

## Example CLI Usage
```bash
python run.py --csv_path="./data/sample/crawl.csv"
