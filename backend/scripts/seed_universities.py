import os
import csv
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, Base, engine
from app.models.university import University


def _safe_float(val):
    try:
        v = str(val).strip().strip('"')
        return float(v) if v else None
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    try:
        v = str(val).strip().strip('"')
        return int(float(v)) if v else None
    except (ValueError, TypeError):
        return None


def _safe_bool(val):
    return str(val).strip().lower() in ("true", "1", "yes")


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    csv_path = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "universities.csv")
    )

    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            inserted = updated = 0
            for row in reader:
                name = row.get("name", "").strip().strip('"')
                if not name:
                    continue

                existing = db.query(University).filter(University.name == name).first()
                obj = existing or University()

                obj.name           = name
                obj.country        = row.get("country", "").strip().strip('"')
                obj.ranking        = _safe_int(row.get("ranking"))
                obj.qs_subject_ranking = _safe_int(row.get("qs_subject_ranking"))
                obj.subject        = row.get("subject", "").strip().strip('"') or None
                obj.tuition        = _safe_float(row.get("tuition"))
                obj.living_cost    = _safe_float(row.get("living_cost"))
                obj.image_url      = row.get("image_url", "").strip().strip('"') or None
                obj.website        = row.get("website", "").strip().strip('"') or None
                obj.description    = row.get("description", "").strip().strip('"') or None
                obj.acceptance_rate = _safe_float(row.get("acceptance_rate"))
                obj.requirements_cgpa = _safe_float(row.get("requirements_cgpa"))
                obj.ielts          = _safe_float(row.get("ielts"))
                obj.toefl          = _safe_int(row.get("toefl"))
                obj.gre_required   = _safe_bool(row.get("gre_required")) if row.get("gre_required") else None
                obj.scholarships   = row.get("scholarships", "").strip().strip('"') or None
                obj.course_duration = _safe_int(row.get("course_duration"))

                if not existing:
                    db.add(obj)
                    inserted += 1
                else:
                    updated += 1

            db.commit()
            print(f"✅ Seeding complete: {inserted} inserted, {updated} updated")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
