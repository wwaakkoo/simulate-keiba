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
    
    # Load model
    model_path = 'models/race_predictor_v1.pkl'
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}")
        return
    
    model = lgb.Booster(model_file=model_path)
    
    # Get test races (latest 10% as in trainer)
    races = db.query(Race).order_by(Race.date).all()
    n = len(races)
    test_races = races[int(n * 0.9):]
    
    print(f"Evaluating on {len(test_races)} test races...")
    
    win_hits = 0
    top3_hits = 0
    correlations = []
    total_races = 0
    
    for race in test_races:
        try:
            result = factory.generate_features_for_race(race.id)
            if not result['features']:
                continue
            
            X = np.array(result['features'])
            preds = model.predict(X)
            
            # Get actual positions
            actuals = []
            for horse_num in result['horse_numbers']:
                entry = next((e for e in race.entries if e.horse_number == horse_num), None)
                if entry and entry.finish_position is not None:
                    actuals.append(entry.finish_position)
                else:
                    actuals.append(9.0) # Placeholder
            
            # 1. Win Rate (Is the horse with lowest predicted position the actual winner?)
            top_pred_idx = np.argmin(preds)
            actual_rank_of_top_pred = actuals[top_pred_idx]
            
            if actual_rank_of_top_pred == 1:
                win_hits += 1
            
            if actual_rank_of_top_pred <= 3:
                top3_hits += 1
                
            # Spearman correlation
            corr, _ = spearmanr(preds, actuals)
            if not np.isnan(corr):
                correlations.append(corr)
            
            total_races += 1
        except Exception as e:
            # print(f"Error in race {race.id}: {e}")
            continue
            
    if total_races > 0:
        win_rate = win_hits / total_races
        top3_rate = top3_hits / total_races
        avg_corr = np.mean(correlations)
        
        print("\n=== Evaluation Results ===")
        print(f"Total Test Races: {total_races}")
        print(f"Win Rate (Top Predicted): {win_rate:.1%}")
        print(f"Top 3 Inclusion Rate: {top3_rate:.1%}")
        print(f"Spearman Rank Correlation: {avg_corr:.3f}")
        print("===========================")
    else:
        print("No races could be evaluated.")
    
    db.close()

if __name__ == "__main__":
    evaluate()
