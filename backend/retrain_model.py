
import os
import sys
import argparse
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.predictor.retraining import IncrementalRetrainer

# Database Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'data', 'keiba.db')
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def main():
    parser = argparse.ArgumentParser(description="Retrain model incrementally.")
    parser.add_argument("--date", type=str, default=None, help="Reference date YYYY-MM-DD (default: today)")
    parser.add_argument("--months", type=int, default=24, help="Lookback months (default: 24)")
    args = parser.parse_args()
    
    if args.date:
        ref_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        ref_date = date.today()
        
    db = SessionLocal()
    try:
        trainer = IncrementalRetrainer(db)
        model = trainer.train_for_date(ref_date, lookback_months=args.months)
        
        if model:
            print("Retraining completed successfully.")
        else:
            print("Retraining failed or no data.")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
