import csv
import os
import random
import re
from typing import Dict, List, Optional, Tuple


QS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "raw_rankings",
    "qs_university_rankings_2025",
    "qs-world-rankings-2025.csv",
)

THE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "raw_rankings",
    "the_world_university_rankings_2016-2026",
    "THE World University Rankings 2016-2026.csv",
)

OUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "universities.csv",
)

FIELDS = [
    "name",
    "country",
    "ranking",
    "qs_subject_ranking",
    "subject",
    "tuition",
    "living_cost",
    "image_url",
    "website",
    "requirements_cgpa",
    "ielts",
    "toefl",
    "gre_required",
    "scholarships",
    "course_duration",
]

SUBJECTS = [
    "Computer Science",
    "Business & Management",
    "Engineering",
    "Medicine",
    "Data Science",
    "Psychology",
    "Economics",
    "Law",
    "Art & Design",
]

SCHOLARSHIPS = [
    "Vice-Chancellor Merit",
    "Dean's Excellence Award",
    "Global Study Grant",
    "",
]


def to_int_rank(value: str) -> Optional[int]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None

    # Handles values like "201-250" or "=45".
    match = re.search(r"\d+", s)
    if not match:
        return None
    return int(match.group(0))


def to_int_year(value: str) -> Optional[int]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    match = re.search(r"\d{4}", s)
    if not match:
        return None
    return int(match.group(0))


def normalize_name(name: str) -> str:
    s = (name or "").strip().lower()
    s = re.sub(r"\([^)]*\)", "", s)  # remove text in brackets
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def key_for(name: str, country: str) -> str:
    return f"{normalize_name(name)}::{(country or '').strip().lower()}"


def load_qs() -> Dict[str, Dict]:
    records: Dict[str, Dict] = {}
    with open(QS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Institution Name") or "").strip()
            country = (row.get("Location Full") or row.get("Location") or "").strip()
            rank = to_int_rank(row.get("2025 Rank", ""))

            if not name or not country:
                continue

            k = key_for(name, country)
            records[k] = {
                "name": name,
                "country": country,
                "qs_rank": rank,
            }
    return records


def load_the_latest_year() -> Tuple[int, Dict[str, Dict]]:
    rows: List[Dict] = []
    max_year = 0

    with open(THE_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = to_int_year(row.get("Year", ""))
            if year is None:
                continue
            max_year = max(max_year, year)
            rows.append(row)

    records: Dict[str, Dict] = {}
    for row in rows:
        year = to_int_year(row.get("Year", ""))
        if year != max_year:
            continue

        name = (row.get("Name") or "").strip()
        country = (row.get("Country") or "").strip()
        rank = to_int_rank(row.get("Rank", ""))

        if not name or not country:
            continue

        k = key_for(name, country)
        records[k] = {
            "name": name,
            "country": country,
            "the_rank": rank,
            "year": max_year,
        }

    return max_year, records


def estimate_costs_inr(country: str, seed: int) -> Tuple[int, int]:
    rng = random.Random(seed)
    c = country.lower()

    if "united states" in c or c == "us":
        return rng.randint(37, 54) * 100000, rng.randint(12, 20) * 100000
    if "united kingdom" in c or c == "uk":
        return rng.randint(26, 42) * 100000, rng.randint(12, 18) * 100000
    if "canada" in c:
        return rng.randint(21, 34) * 100000, rng.randint(9, 12) * 100000
    if "australia" in c:
        return rng.randint(22, 33) * 100000, rng.randint(11, 16) * 100000
    if "singapore" in c or "hong kong" in c:
        return rng.randint(18, 30) * 100000, rng.randint(10, 16) * 100000
    if "germany" in c or "france" in c or "finland" in c:
        return rng.randint(2, 10) * 100000, rng.randint(8, 14) * 100000
    return rng.randint(15, 30) * 100000, rng.randint(8, 15) * 100000


def synthetic_fields(name: str, country: str, base_rank: Optional[int]) -> Dict:
    seed = abs(hash(f"{name}-{country}")) % (10**8)
    rng = random.Random(seed)

    tuition, living = estimate_costs_inr(country, seed)
    subject = SUBJECTS[seed % len(SUBJECTS)]
    req_cgpa = round(rng.uniform(6.5, 9.5), 1)
    ielts = rng.choice([6.0, 6.5, 7.0, 7.5])
    toefl = rng.choice([80, 85, 90, 95, 100, 105, 110])
    gre_required = rng.random() < 0.4
    scholarship = SCHOLARSHIPS[seed % len(SCHOLARSHIPS)]
    duration = rng.choice([12, 18, 24, 36, 48])

    domain_hint = re.sub(r"[^a-z0-9]", "", normalize_name(name).replace(" ", ""))
    image_url = f"https://logo.clearbit.com/{domain_hint}.edu" if domain_hint else ""

    qs_subject_rank = base_rank if base_rank is not None else rng.randint(50, 400)

    return {
        "subject": subject,
        "tuition": tuition,
        "living_cost": living,
        "image_url": image_url,
        "website": "",
        "requirements_cgpa": req_cgpa,
        "ielts": ielts,
        "toefl": toefl,
        "gre_required": gre_required,
        "scholarships": scholarship,
        "course_duration": duration,
        "qs_subject_ranking": qs_subject_rank,
    }


def combine_rank(qs_rank: Optional[int], the_rank: Optional[int]) -> Optional[int]:
    vals = [v for v in [qs_rank, the_rank] if v is not None]
    if not vals:
        return None
    return int(round(sum(vals) / len(vals)))


def build_dataset() -> None:
    if not os.path.exists(QS_PATH):
        raise FileNotFoundError(f"Missing QS file: {QS_PATH}")
    if not os.path.exists(THE_PATH):
        raise FileNotFoundError(f"Missing THE file: {THE_PATH}")

    qs = load_qs()
    the_year, the = load_the_latest_year()

    all_keys = set(qs.keys()) | set(the.keys())

    merged_rows: List[Dict] = []
    for k in all_keys:
        qs_item = qs.get(k, {})
        the_item = the.get(k, {})

        name = qs_item.get("name") or the_item.get("name")
        country = qs_item.get("country") or the_item.get("country")
        qs_rank = qs_item.get("qs_rank")
        the_rank = the_item.get("the_rank")

        if not name or not country:
            continue

        final_rank = combine_rank(qs_rank, the_rank)
        extra = synthetic_fields(name, country, qs_rank or final_rank)

        merged_rows.append(
            {
                "name": name,
                "country": country,
                "ranking": final_rank,
                "qs_subject_ranking": extra["qs_subject_ranking"],
                "subject": extra["subject"],
                "tuition": extra["tuition"],
                "living_cost": extra["living_cost"],
                "image_url": extra["image_url"],
                "website": extra["website"],
                "requirements_cgpa": extra["requirements_cgpa"],
                "ielts": extra["ielts"],
                "toefl": extra["toefl"],
                "gre_required": extra["gre_required"],
                "scholarships": extra["scholarships"],
                "course_duration": extra["course_duration"],
            }
        )

    merged_rows.sort(key=lambda r: (r["ranking"] is None, r["ranking"] or 10**9, r["name"]))

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(merged_rows)

    print(f"THE latest year selected: {the_year}")
    print(f"QS rows loaded: {len(qs)}")
    print(f"THE rows loaded ({the_year}): {len(the)}")
    print(f"Merged unique universities: {len(merged_rows)}")
    print(f"Output written to: {OUT_PATH}")


if __name__ == "__main__":
    build_dataset()
