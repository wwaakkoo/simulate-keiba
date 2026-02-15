
import os
import sys
import pandas as pd
import numpy as np
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import lightgbm as lgb

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.race import Race
from app.predictor.features import FeatureFactory
from app.predictor.betting import VarianceReductionStrategy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'data', 'keiba.db')
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def main():
    db = SessionLocal()
    factory = FeatureFactory(db)
    
    print("Fetching 2025 Jan Data...")
    races_2025 = db.query(Race).filter(
        Race.date >= date(2025, 1, 1),
        Race.date <= date(2025, 1, 31)
    ).all()
    
    if not races_2025:
        print("No races found for 2025 Jan.")
        return

    # Train Model (Up to 2024)
    # Ideally load a saved model, but for strict verification let's retrain quickly or assume model exists?
    # Doing a quick retrain on 2024 data (subset) for speed, or load validatoin logic?
    # Let's use the IncrementalRetrainer to get a model for 2025-01-01!
    from app.predictor.retraining import IncrementalRetrainer
    trainer = IncrementalRetrainer(db)
    
    # Train/Load model
    model_path = os.path.join("models/incremental", "model_20250101.txt")
    if os.path.exists(model_path):
        print(f"Loading existing model: {model_path}")
        model = lgb.Booster(model_file=model_path)
    else:
        print("Training model for 2025-01-01...")
        model = trainer.train_for_date(date(2025, 1, 1), lookback_months=24)
        
    if not model:
        print("Failed to train model.")
        return

    # Predict & Simulate
    print(f"Simulating {len(races_2025)} races...")
    
    strategies = {
        'flat': lambda p: [{'bet_amount': 100} for _ in p], # Simple flat
        'low_variance': VarianceReductionStrategy('low_variance'),
        'high_volume': VarianceReductionStrategy('high_volume')
    }
    
    results = {name: {'bets': 0, 'return': 0, 'invest': 0, 'hits': 0} for name in strategies}
    
    for race in races_2025:
        try:
            # Features
            feat_res = factory.generate_features_for_race(race.id)
            if not feat_res['features']:
                continue
                
            X = np.array(feat_res['features'])
            preds = model.predict(X)
            
            # Map back to entries
            race_preds = []
            entries_map = {e.horse_number: e for e in race.entries}
            
            for i, score in enumerate(preds):
                h_num = feat_res['horse_numbers'][i]
                entry = entries_map.get(h_num)
                if not entry: continue
                
                # Pseudo probability (softmax over score? or use model output if objective=binary)
                # Lambdarank output is score, not prob.
                # Need conversion? or just use score for ranking.
                # Strategies assume 'win_prob'.
                # For LambdaRank, we don't have direct prob.
                # Approximation: Softmax of scores? Or just normalize?
                # Let's use simple normalization for now: scores -> exp(scores) / sum
                pass

            # Fix: Model output is raw score. We need probabilities for Kelly/Strategies.
            # Strategy expects 'win_prob'.
            # Hack: Softmax normalization of scores for now.
            
            exp_preds = np.exp(preds)
            probs = exp_preds / np.sum(exp_preds)
            
            for i, prob in enumerate(probs):
                h_num = feat_res['horse_numbers'][i]
                entry = entries_map.get(h_num)
                if not entry: continue
                
                race_preds.append({
                    'horse_number': h_num,
                    'win_prob': prob,
                    'odds': float(entry.odds) if entry.odds else 0.0,
                    'finish_position': entry.finish_position
                })
            
            # Apply Strategies
            for name, strategy in strategies.items():
                if name == 'flat':
                    # Top 1
                    sorted_preds = sorted(race_preds, key=lambda x: x['win_prob'], reverse=True)
                    bet_decisions = []
                    if sorted_preds:
                        # Bet 100 on Top 1
                        bet_decisions = [{'horse_number': sorted_preds[0]['horse_number'], 'bet_amount': 100}]
                else:
                    bet_decisions = strategy.evaluate(race_preds)
                
                for bet in bet_decisions:
                    amt = bet.get('bet_amount', 0)
                    if amt > 0:
                        results[name]['invest'] += amt
                        results[name]['bets'] += 1
                        
                        # Check result
                        # Find entry result
                        if bet.get('bet_type'):
                            # Complex betting (skip for now, assume Win)
                            pass
                        else:
                            # Standard Win bet
                            h_num = bet['horse_number']
                            target = next((p for p in race_preds if p['horse_number'] == h_num), None)
                            if target and target['finish_position'] == 1:
                                refund = amt * target['odds']
                                results[name]['return'] += refund
                                results[name]['hits'] += 1

        except Exception as e:
            # print(e)
            continue

    print("\n=== Simulation Results (2025 Jan) ===")
    for name, res in results.items():
        roi = (res['return'] - res['invest']) / res['invest'] * 100 if res['invest'] > 0 else 0
        win_rate = res['hits'] / res['bets'] * 100 if res['bets'] > 0 else 0
        print(f"Strategy: {name}")
        print(f"  Bets: {res['bets']}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  ROI: {roi:.1f}%")
        print(f"  Profit: {res['return'] - res['invest']}")
        print("-" * 20)

if __name__ == "__main__":
    main()
