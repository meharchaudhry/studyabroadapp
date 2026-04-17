import json
import os
import re
from datetime import datetime
from typing import Dict, Tuple

import requests
from bs4 import BeautifulSoup


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def _load_visa_catalog() -> Dict[str, Dict]:
    path = os.path.join(_repo_root(), "data", "visa_data.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("countries", {})


def _fetch_official_page(url: str) -> Tuple[str, bool, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for node in soup(["script", "style", "noscript", "svg", "img", "iframe"]):
            node.decompose()

        text_parts = []
        for selector in ["h1", "h2", "h3", "h4", "p", "li"]:
            for element in soup.select(selector):
                text = element.get_text(" ", strip=True)
                if text:
                    text_parts.append(text)

        text = "\n".join(text_parts)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if len(text) < 200:
            text = soup.get_text("\n", strip=True)
            text = re.sub(r"\n{3,}", "\n\n", text).strip()

        if len(text) > 20000:
            text = text[:20000] + "\n\n[truncated]"

        return text, True, "fetched"
    except Exception as exc:
        return "", False, str(exc)


def _fallback_markdown(country: str, meta: Dict[str, object]) -> str:
    checklist = meta.get("checklist", []) or []
    lines = [
        f"# {country} Student Visa",
        "",
        f"Official Link: {meta.get('official_link', '')}",
        f"Processing Time: {meta.get('processing_time', '')}",
        f"Visa Fee (INR): {meta.get('visa_fee_inr', '')}",
        "",
        "## Checklist",
    ]
    for item in checklist:
        lines.append(f"- [{item.get('category', 'Other')}] {item.get('item', '')}")
    return "\n".join(lines).strip() + "\n"


def _build_markdown(country: str, meta: Dict[str, object], extracted_text: str, fetch_status: str) -> str:
    checklist = meta.get("checklist", []) or []
    lines = [
        f"# {country} Student Visa",
        "",
        f"Official Link: {meta.get('official_link', '')}",
        f"Processing Time: {meta.get('processing_time', '')}",
        f"Visa Fee (INR): {meta.get('visa_fee_inr', '')}",
        f"Source Fetch Status: {fetch_status}",
        f"Last Refreshed (UTC): {datetime.utcnow().isoformat()}Z",
        "",
        "## Checklist",
    ]
    for item in checklist:
        lines.append(f"- [{item.get('category', 'Other')}] {item.get('item', '')}")

    if extracted_text:
        lines.extend([
            "",
            "## Extracted Official Page Text",
            extracted_text,
        ])
    else:
        lines.extend([
            "",
            "## Fallback Summary",
            _fallback_markdown(country, meta),
        ])

    return "\n".join(lines).strip() + "\n"


def scrape_visas() -> None:
    docs_dir = os.path.join(_repo_root(), "data", "visa_docs")
    os.makedirs(docs_dir, exist_ok=True)

    catalog = _load_visa_catalog()
    manifest = []

    for country, meta in catalog.items():
        official_link = meta.get("official_link", "")
        extracted_text = ""
        fetch_ok = False
        fetch_note = ""

        if official_link:
            extracted_text, fetch_ok, fetch_note = _fetch_official_page(str(official_link))

        filename = f"{_slugify(country)}_student_visa.md"
        content = _build_markdown(country, meta, extracted_text if fetch_ok else "", fetch_note if official_link else "no_official_link")

        with open(os.path.join(docs_dir, filename), "w", encoding="utf-8") as f:
            f.write(content)

        manifest.append(
            {
                "country": country,
                "file": filename,
                "official_link": official_link,
                "fetch_ok": fetch_ok,
                "fetch_note": fetch_note,
            }
        )

    manifest_path = os.path.join(docs_dir, "_refresh_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"generated_at_utc": datetime.utcnow().isoformat() + "Z", "countries": manifest}, f, indent=2)

    print(f"✅ Compiled visa documents for {len(manifest)} countries into {docs_dir}")
    print(f"✅ Refresh manifest written to {manifest_path}")


if __name__ == "__main__":
    scrape_visas()
