import os
import csv
import sys

# Make sure we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, Base, engine
from app.models.university import University

def str_to_bool(val: str) -> bool:
    return str(val).strip().lower() in ("true", "1", "yes")

def seed():
    # Create tables if not exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "universities.csv")
    csv_path = os.path.normpath(csv_path)

    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            inserted = 0
            updated = 0
            for row in reader:
                name = row["name"].strip()
                if not name:
                    continue

                existing = db.query(University).filter(University.name == name).first()
                obj = existing or University()
                
                obj.name = name
                obj.country = row.get("country", "").strip()
                obj.ranking = int(row["ranking"]) if row.get("ranking") else None
                obj.qs_subject_ranking = int(row["qs_subject_ranking"]) if row.get("qs_subject_ranking") else None
                obj.subject = row.get("subject", "").strip() or None
                obj.tuition = float(row["tuition"]) if row.get("tuition") else None
                obj.living_cost = float(row["living_cost"]) if row.get("living_cost") else None
                obj.image_url = row.get("image_url", "").strip() or None
                obj.website = row.get("website", "").strip() or None
                obj.requirements_cgpa = float(row["requirements_cgpa"]) if row.get("requirements_cgpa") else None
                obj.ielts = float(row["ielts"]) if row.get("ielts") else None
                obj.toefl = int(row["toefl"]) if row.get("toefl") else None
                obj.gre_required = str_to_bool(row["gre_required"]) if row.get("gre_required") else None
                obj.scholarships = row.get("scholarships", "").strip() or None
                obj.course_duration = int(row["course_duration"]) if row.get("course_duration") else None

                if not existing:
                    db.add(obj)
                    inserted += 1
                else:
                    updated += 1

            db.commit()
            print(f"✅ Seeding complete: {inserted} inserted, {updated} updated")
    except Exception as e:
        db.rollback()
        print(f"❌ Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
