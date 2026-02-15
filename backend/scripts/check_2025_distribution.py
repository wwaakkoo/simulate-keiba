
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
        results = db.query(
            func.strftime('%Y-%m', Race.date).label('month'),
            func.count(Race.id)
        ).filter(
            Race.date >= date(2025, 1, 1),
            Race.date <= date(2025, 12, 31)
        ).group_by('month').order_by('month').all()
        
        print("2025 Race Distribution:")
        for month, count in results:
            print(f"{month}: {count} races")
            
        latest_race = db.query(Race).order_by(Race.date.desc()).first()
        if latest_race:
             print(f"Latest Race Overall: {latest_race.date}")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
