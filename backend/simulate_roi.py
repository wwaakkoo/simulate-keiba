import os
import sys
import numpy as np
from sqlalchemy import select
from app.predictor.sync_database import SessionLocal
from app.predictor.features import FeatureFactory
from app.models.race import Race
from app.models.race_entry import RaceEntry
import lightgbm as lgb
import xgboost as xgb

# Add backend to path
sys.path.append(os.getcwd())

class BettingSimulator:
    def __init__(self, db, initial_capital=10000):
        self.db = db
        self.factory = FeatureFactory(db)
        self.capital = initial_capital
        
        # Load models
        self.lgb_model = lgb.Booster(model_file='models/race_predictor_lgb.pkl')
        self.xgb_model = xgb.XGBRanker()
        self.xgb_model.load_model('models/race_predictor_xgb.json')
        
    def normalize(self, scores):
        if np.max(scores) == np.min(scores): return scores
        return (scores - np.min(scores)) / (np.max(scores) - np.min(scores))

    def run_simulation(self, races_subset, strategy='top1'):
        total_bets = 0
        total_cost = 0
        total_return = 0
        win_count = 0
        
        print(f"Simulating strategy: {strategy} on {len(races_subset)} races...")
        
        for race in races_subset:
            try:
                result = self.factory.generate_features_for_race(race.id)
                if not result['features']:
                    continue
                
                X = np.array(result['features'])
                lgb_preds = self.lgb_model.predict(X)
                xgb_preds = self.xgb_model.predict(X)
                
                # Ensemble score
                scores = 0.5 * self.normalize(lgb_preds) + 0.5 * self.normalize(xgb_preds)
                
                top_idx = np.argmax(scores)
                
                # Get entry for top predicted horse
                horse_num = result['horse_numbers'][top_idx]
                entry = next((e for e in race.entries if e.horse_number == horse_num), None)
                
                if not entry or entry.odds is None:
                    continue
                    
                total_bets += 1
                bet_amount = 100
                total_cost += bet_amount
                
                if entry.finish_position == 1:
                    win_count += 1
                    total_return += bet_amount * entry.odds
                    
            except Exception:
                continue
                
        roi = (total_return / total_cost * 100) if total_cost > 0 else 0
        hit_rate = (win_count / total_bets * 100) if total_bets > 0 else 0
        
        return {
            "total_bets": total_bets,
            "win_count": win_count,
            "total_cost": total_cost,
            "total_return": total_return,
            "hit_rate": hit_rate,
            "roi": roi
        }

def main():
    db = SessionLocal()
    # Use test set (last 10%)
    races = db.query(Race).order_by(Race.date).all()
    n = len(races)
    test_races = races[int(n * 0.9):]
    
    simulator = BettingSimulator(db)
    
    results = simulator.run_simulation(test_races, strategy='top1_win_bet')
    
    print("\n=== ROI Simulation Results ===")
    print(f"Total Bets: {results['total_bets']}")
    print(f"Wins: {results['win_count']}")
    print(f"Hit Rate: {results['hit_rate']:.1f}%")
    print(f"Total Cost: {results['total_cost']:,} yen")
    print(f"Total Return: {results['total_return']:,} yen")
    print(f"ROI: {results['roi']:.1f}%")
    print("==============================")
    
    db.close()

if __name__ == "__main__":
    main()
