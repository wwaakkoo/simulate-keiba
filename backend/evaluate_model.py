import os
import sys
import lightgbm as lgb
import numpy as np
from sqlalchemy import select
from app.predictor.sync_database import SessionLocal
from app.predictor.features import FeatureFactory
from app.models.race import Race
from app.models.race_entry import RaceEntry
from scipy.stats import spearmanr

# Add backend to path
sys.path.append(os.getcwd())

def evaluate():
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
        print("Loaded LightGBM model")
    
    if os.path.exists(xgb_path):
        import xgboost as xgb_lib
        xgb_model = xgb_lib.XGBRanker()
        xgb_model.load_model(xgb_path)
        print("Loaded XGBoost model")
        
    if not lgb_model and not xgb_model:
        print("No models found.")
        return
    
    # Get test races
    races = db.query(Race).order_by(Race.date).all()
    n = len(races)
    test_races = races[int(n * 0.9):]
    
    print(f"Evaluating on {len(test_races)} test races...")
    
    results = {
        'lgb': {'win_hits': 0, 'top3_hits': 0},
        'xgb': {'win_hits': 0, 'top3_hits': 0},
        'ensemble': {'win_hits': 0, 'top3_hits': 0}
    }
    total_races = 0
    
    for race in test_races:
        try:
            result = factory.generate_features_for_race(race.id)
            if not result['features']:
                continue
            
            X = np.array(result['features'])
            actuals = []
            for horse_num in result['horse_numbers']:
                entry = next((e for e in race.entries if e.horse_number == horse_num), None)
                actuals.append(entry.finish_position if (entry and entry.finish_position is not None) else 99)

            def get_hits(preds, actuals):
                top_idx = np.argmax(preds)
                win = 1 if actuals[top_idx] == 1 else 0
                top3 = 1 if actuals[top_idx] <= 3 else 0
                return win, top3

            def normalize(scores):
                if np.max(scores) == np.min(scores): return scores
                return (scores - np.min(scores)) / (np.max(scores) - np.min(scores))

            preds_lgb = lgb_model.predict(X) if lgb_model else None
            preds_xgb = xgb_model.predict(X) if xgb_model else None
            
            if preds_lgb is not None:
                win, top3 = get_hits(preds_lgb, actuals)
                results['lgb']['win_hits'] += win
                results['lgb']['top3_hits'] += top3
                
            if preds_xgb is not None:
                win, top3 = get_hits(preds_xgb, actuals)
                results['xgb']['win_hits'] += win
                results['xgb']['top3_hits'] += top3
                
            if preds_lgb is not None and preds_xgb is not None:
                # Weighted Ensemble
                ens_preds = 0.6 * normalize(preds_lgb) + 0.4 * normalize(preds_xgb)
                win, top3 = get_hits(ens_preds, actuals)
                results['ensemble']['win_hits'] += win
                results['ensemble']['top3_hits'] += top3
            
            total_races += 1
        except Exception as e:
            # print(f"Error: {e}")
            continue
            
    if total_races > 0:
        print("\n=== Evaluation Results ===")
        print(f"Total Test Races: {total_races}")
        for key in ['lgb', 'xgb', 'ensemble']:
            w = results[key]['win_hits'] / total_races
            t3 = results[key]['top3_hits'] / total_races
            print(f"[{key.upper()}] Win Rate: {w:.1%}, Top 3 Rate: {t3:.1%}")
        print("===========================")
    
    db.close()

if __name__ == "__main__":
    evaluate()

if __name__ == "__main__":
    evaluate()
