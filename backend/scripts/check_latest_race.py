
import os
import sys
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import date

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.race import Race

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'data', 'keiba.db')
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def main():
    db = SessionLocal()
    try:
        latest_race = db.query(Race).order_by(Race.date.desc()).first()
        count_2025 = db.query(Race).filter(Race.date >= date(2025, 1, 1)).count()
        
        if latest_race:
            print(f"Latest Race Date: {latest_race.date}")
            print(f"Total races in 2025: {count_2025}")
        else:
            print("No races found.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
