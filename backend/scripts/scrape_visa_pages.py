import json
import os
import re
from pathlib import Path
import requests
import html2text
import sys

# Allow running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_project_root() -> Path:
    """Gets the absolute path to the project root directory."""
    return Path(__file__).parent.parent

def get_visa_urls_from_source_file() -> list[dict]:
    """Extracts visa page URLs from the source JSON file."""
    root = get_project_root()
    source_file_path = root / "data" / "visa_source_urls.json"
    
    urls = []
    try:
        with open(source_file_path, "r", encoding="utf-8") as f:
            urls_data = json.load(f)
        
        for item in urls_data:
            if "url" in item and "country" in item:
                # Create a clean name from the URL and country
                name = f"{item['country']}_{item['url'].split('/')[-1] or item['url'].split('/')[-2]}"
                name = re.sub(r'[^\w_]', '', name) # Sanitize name
                urls.append({"name": name, "url": item["url"]})

    except FileNotFoundError:
        print(f"❌ Error: Visa source file not found at {source_file_path}")
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from {source_file_path}")
    except Exception as e:
        print(f"❌ Error reading or parsing visa source file: {e}")
    
    return urls

def scrape_and_save_visa_pages():
    """Fetches visa info pages and saves them as Markdown files."""
    root = get_project_root()
    output_dir = root / "data" / "visa_docs"
    output_dir.mkdir(exist_ok=True)

    urls_to_fetch = get_visa_urls_from_source_file()
    if not urls_to_fetch:
        print("⚠️ No URLs found in the source file. Cannot scrape.")
        return

    print(f"🚀 Starting visa page scraping for {len(urls_to_fetch)} URLs...")

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.body_width = 0
    
    success_count = 0
    fail_count = 0

    for item in urls_to_fetch:
        name, url = item["name"], item["url"]
        filename = f"{name}.md"
        file_path = output_dir / filename
        
        try:
            print(f"  Scraping: {url}")
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=45)
            response.raise_for_status()
            
            html_content = response.text
            markdown_content = h.handle(html_content)
            
            markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"  ✅ Saved to: data/visa_docs/{filename}")
            success_count += 1

        except requests.RequestException as e:
            print(f"  ❌ Failed to fetch {url}: {e}")
            fail_count += 1
        except Exception as e:
            print(f"  ❌ An error occurred for {url}: {e}")
            fail_count += 1

    print(f"\n✅ Visa scraping process complete. Successfully scraped {success_count} pages. Failed {fail_count} pages.")

if __name__ == "__main__":
    scrape_and_save_visa_pages()
