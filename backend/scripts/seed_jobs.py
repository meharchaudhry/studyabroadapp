import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from seed_db import seed_jobs


def main() -> None:
    db = SessionLocal()
    try:
        seed_jobs(db)
        print("Done seeding jobs.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
