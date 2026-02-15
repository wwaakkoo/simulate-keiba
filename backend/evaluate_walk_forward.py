
import os
import sys
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.predictor.validation import WalkForwardValidator

# Database Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/
PROJECT_ROOT = os.path.dirname(BASE_DIR) # repo root
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'data', 'keiba.db')
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def main():
    db = SessionLocal()
    try:
        # Config: Train 2 years, Test 3 months, Step 3 months
        # For speed in debug, maybe smaller? But user wants real metrics.
        # Let's stick to plan.
        
        validator = WalkForwardValidator(
            db=db,
            initial_train_months=24,
            test_months=3,
            step_months=3
        )
        
        df_results = validator.run()
        
        print("\n=== Walk-Forward Validation Summary ===")
        print(df_results)
        
        if not df_results.empty:
            print(f"\nAverage Win Rate: {df_results['win_rate'].mean():.2%}")
            print(f"Average ROI: {df_results['roi'].mean():.2%}")
            print(f"Total Profit: ¥{df_results['profit'].sum():,}")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
