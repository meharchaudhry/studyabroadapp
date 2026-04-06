import os
import sys
import csv

# Ensure app is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.university import University
from app.models.job import Job

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def seed_universities(db: Session):
    csv_file = os.path.join(DATA_DIR, "universities.csv")
    if not os.path.exists(csv_file):
        print(f"File not found: {csv_file}")
        return

    print("Seeding universities...")
    with open(csv_file, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        count = 0
        for row in reader:
            uni = db.query(University).filter(University.name == row['name']).first()
            if not uni:
                new_uni = University(
                    name=row['name'],
                    country=row['country'],
                    ranking=int(row['ranking']) if row['ranking'] else None,
                    tuition=float(row['tuition']) if row['tuition'] else 0.0,
                    living_cost=float(row['living_cost']) if row['living_cost'] else 0.0
                )
                db.add(new_uni)
                count += 1
        db.commit()
        print(f"Added {count} universities.")

def seed_jobs(db: Session):
    csv_file = os.path.join(DATA_DIR, "local_jobs.csv")
    if not os.path.exists(csv_file):
        print(f"File not found: {csv_file}")
        return

    print("Seeding local jobs...")
    with open(csv_file, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        count = 0
        for row in reader:
            job_id = f"local_{count}"
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                new_job = Job(
                    id=job_id,
                    title=row['title'],
                    company=row['company'],
                    location=row['location'],
                    salary=row['salary'],
                    job_type=row['job_type'],
                    source="local",
                    apply_url=row['apply_link']
                )
                db.add(new_job)
                count += 1
        db.commit()
        print(f"Added {count} local jobs.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_universities(db)
        seed_jobs(db)
        print("Done seeding.")
    finally:
        db.close()
