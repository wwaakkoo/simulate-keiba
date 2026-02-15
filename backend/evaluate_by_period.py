import os
import sys
import numpy as np
from app.predictor.sync_database import SessionLocal
from app.predictor.features import FeatureFactory
from app.models.race import Race
from app.models.race_entry import RaceEntry
from datetime import datetime

# Add backend to path
sys.path.append(os.getcwd())

def evaluate_by_period():
    db = SessionLocal()
    factory = FeatureFactory(db)
    
    # Load models
    lgb_path = 'models/race_predictor_lgb.pkl'
    xgb_path = 'models/race_predictor_xgb.json'
    
    lgb_model = None
    xgb_model = None
    
    if os.path.exists(lgb_path):
        import lightgbm as lgb_lib
        lgb_model = lgb_lib.Booster(model_file=lgb_path)
    
    if os.path.exists(xgb_path):
        import xgboost as xgb_lib
        xgb_model = xgb_lib.XGBRanker()
        xgb_model.load_model(xgb_path)
        
    if not lgb_model and not xgb_model:
        print("No models found.")
        return
    
    # Analyze periods
    races = db.query(Race).order_by(Race.date).all()
    if not races:
        print("No races found in DB.")
        return

    # Use the same split as trainer for fairness (last 10% is usually test)
    n = len(races)
    test_start_idx = int(n * 0.9)
    test_races = races[test_start_idx:]
    
    print(f"Total races in DB: {len(races)}")
    print(f"Test split start: {races[test_start_idx].date}")
    print(f"Evaluating on {len(test_races)} test races by year...")
    
    # Group test races by year
    test_races_by_year = {}
    for r in test_races:
        year = r.date.year
        if year not in test_races_by_year:
            test_races_by_year[year] = []
        test_races_by_year[year].append(r)

    def get_hits(preds, actuals):
        top_idx = np.argmax(preds)
        win = 1 if actuals[top_idx] == 1 else 0
        top3 = 1 if actuals[top_idx] <= 3 else 0
        return win, top3

    def normalize(scores):
        if np.max(scores) == np.min(scores): return scores
        return (scores - np.min(scores)) / (np.max(scores) - np.min(scores))

    for year in sorted(test_races_by_year.keys()):
        results = {'win_hits': 0, 'top3_hits': 0, 'count': 0}
        
        for race in test_races_by_year[year]:
            try:
                result = factory.generate_features_for_race(race.id)
                if not result['features']: continue
                
                X = np.array(result['features'])
                actuals = []
                for horse_num in result['horse_numbers']:
                    entry = next((e for e in race.entries if e.horse_number == horse_num), None)
                    actuals.append(entry.finish_position if (entry and entry.finish_position is not None) else 99)

                preds_lgb = lgb_model.predict(X) if lgb_model else None
                preds_xgb = xgb_model.predict(X) if xgb_model else None
                
                if preds_lgb is not None and preds_xgb is not None:
                    ens_preds = 0.6 * normalize(preds_lgb) + 0.4 * normalize(preds_xgb)
                elif preds_lgb is not None:
                    ens_preds = preds_lgb
                else:
                    ens_preds = preds_xgb
                
                win, top3 = get_hits(ens_preds, actuals)
                results['win_hits'] += win
                results['top3_hits'] += top3
                results['count'] += 1
            except:
                continue
        
        if results['count'] > 0:
            w = results['win_hits'] / results['count']
            t3 = results['top3_hits'] / results['count']
            print(f"Year {year}: {results['count']} races, Win: {w:.1%}, Top3: {t3:.1%}")

    db.close()

if __name__ == "__main__":
    evaluate_by_period()
