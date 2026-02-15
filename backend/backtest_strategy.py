import os
import sys
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.race import Race
from app.models.race_entry import RaceEntry
from app.predictor.inference import InferenceEngine
from app.predictor.betting import KellyBettingStrategy

# Database Setup
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__)) # .../backend
PROJECT_ROOT = os.path.dirname(BACKEND_DIR) # .../simulate-keiba
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'data', 'keiba.db')
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Backtester:
    def __init__(self, start_date: date, end_date: date, initial_bankroll: int = 1000000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_bankroll = initial_bankroll
        self.bankroll = initial_bankroll
        self.db = SessionLocal()
        
        # Initialize Engine
        # Note: In a real simulation, we should retrain/update models periodically.
        # Here we assume the current model is "fixed" for the test period
        # or represents the "production" model at that time.
        self.inference_engine = InferenceEngine()
        
        # Override Strategy parameters if needed for testing scenarios
        # self.inference_engine.kelly.min_prob = 0.05 
        
        self.results = []
        self.history = [] # For plotting

    def run(self):
        print(f"Starting Backtest from {self.start_date} to {self.end_date}")
        print(f"Initial Bankroll: ¥{self.initial_bankroll:,}")
        
        # Fetch Races
        races = self.db.query(Race).filter(
            Race.date >= self.start_date,
            Race.date <= self.end_date
        ).order_by(Race.date).all()
        
        print(f"Found {len(races)} races.")
        
        total_bets = 0
        skipped_races = 0
        
        for race in tqdm(races):
            # 1. Predict
            try:
                # We interpret using the inference engine which uses FeatureFactory.
                # FeatureFactory respects race.date (only uses past data).
                prediction_response = self.inference_engine.predict_race(race.race_id, self.db)
                
                # The response contains 'predictions' with 'mark' and 'bet_amount' (parsed from mark?)
                # Actually, InferenceEngine calculates bet_amount internally but returns PredictionItem.
                # PredictionItem has 'mark' string like "BUY ¥1000".
                # We need the raw betting data. 
                # InferenceEngine.predict_race returns PredictionResponse.
                # Let's verify inference.py to see if we can get structured data.
                # Currently it returns PredictionResponse with List[PredictionItem].
                # PredictionItem has metadata but not raw EV/Prob in structured form easily usable?
                # Actually, check schemas.py. PredictionItem has 'mark'.
                # We might need to parse 'mark' OR modify InferenceEngine to return raw data for backtest.
                
                # Hack: Parse 'mark' or just trust the strategy inside?
                # Better: Allow InferenceEngine to return raw dicts if requested, or access strategy directly?
                # Actually, `predict_race` calls `kelly.evaluate`.
                # Let's parse the `mark` from PredictionItem.
                # Format: "BUY ¥{amount}" or ""
                
                bet_placed = False
                
                for pred in prediction_response.predictions:
                    if "BUY" in pred.mark:
                        # Extract amount
                        import re
                        match = re.search(r"BUY ¥(\d+)", pred.mark)
                        if match:
                            amount = int(match.group(1))
                            if amount > 0:
                                self._place_bet(race, pred, amount)
                                total_bets += 1
                                bet_placed = True
                
                if not bet_placed:
                    skipped_races += 1
                    
            except Exception as e:
                # print(f"Error processing race {race.race_id}: {e}")
                continue
                
            # Update History (Daily? Per race?)
            self.history.append({
                'date': race.date,
                'bankroll': self.bankroll
            })
            
            # Bankruptcy Check
            if self.bankroll <= 0:
                print("⚠️ BANKRUPT!")
                break
                
        self._print_summary()

    def _place_bet(self, race: Race, pred: Any, amount: int):
        # 1. Deduct Bet
        if amount > self.bankroll:
             amount = self.bankroll # All-in if insufficient (or skip?)
             # Kelly implies fraction of CURRENT bankroll. 
             # But the amount calculated by strategy used the INTERNAL bankroll of the strategy instance.
             # We need to sync the strategy's bankroll with the backtester's bankroll.
             pass

        # Sync Bankroll logic:
        # The Strategy object inside Inference Engine maintains its own bankroll?
        # Let's check betting.py.
        # KellyBettingStrategy has `self.bankroll`.  We need to update it!
        
        # IMPORTANT: We must inject current bankroll into strategy before calculating?
        # InferenceEngine doesn't accept bankroll param in predict_race.
        # We should update `inference_engine.kelly.bankroll` before prediction?
        # Yes.
        
        # Wait, if I do `step 1: predict`, the strategy uses *stale* or *default* bankroll.
        # I need to set `self.inference_engine.kelly.bankroll = self.bankroll` BEFORE `predict_race`.
        
        # Deduct Cost
        self.bankroll -= amount
        
        # 2. Check Result
        # Find the horse in race entries
        # pred.horse_id is usually the netkeiba ID (string). e.horse_id is internal integer PK.
        # We need to compare with e.horse.horse_id
        entry = next((e for e in race.entries if e.horse and e.horse.horse_id == str(pred.horse_id)), None)
        
        return_amount = 0
        result = "LOSE"
        actual_rank = entry.finish_position if entry and entry.finish_position else 99
        
        # Simple Win Betting
        if entry:
            # print(f"       Actual Rank: {entry.finish_position}, Odds: {entry.odds}, Horse: {entry.horse.name if entry.horse else 'Unknown'}")
            pass
        else:
            # print(f"       ENTRY NOT FOUND for Horse ID {pred.horse_id}")
            pass
            
        # Simple Win Betting
        if actual_rank == 1:
            odds = float(entry.odds) if entry.odds else 1.0
            return_amount = int(amount * odds)
            result = "WIN"
        
        self.bankroll += return_amount
        
        # Log
        self.results.append({
            'race_id': race.race_id,
            'date': race.date,
            'horse': pred.horse_name,
            'bet_amount': amount,
            'odds': float(entry.odds) if entry else 0.0,
            'result': result,
            'return': return_amount,
            'balance': self.bankroll,
            'rank': actual_rank
        })
        
        # Update Strategy Bankroll for next race
        self.inference_engine.kelly.bankroll = self.bankroll

    def _print_summary(self):
        df = pd.DataFrame(self.results)
        if df.empty:
            print("No bets placed.")
            return

        total_invested = df['bet_amount'].sum()
        total_return = df['return'].sum()
        profit = total_return - total_invested
        roi = (total_return / total_invested) * 100 if total_invested > 0 else 0
        win_rate = (df['result'] == 'WIN').mean() * 100
        
        print("\n=== Backtest Summary ===")
        print(f"Period: {self.start_date} ~ {self.end_date}")
        print(f"Final Bankroll: ¥{self.bankroll:,} (Profit: ¥{profit:,})")
        print(f"ROI: {roi:.2f}%")
        print(f"Hit Rate: {win_rate:.2f}%")
        print(f"Total Bets: {len(df)}")
        print(f"Max Bet: ¥{df['bet_amount'].max():,}")
        
        # Monthly Summary
        df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
        monthly = df.groupby('month').agg({
            'bet_amount': 'sum',
            'return': 'sum',
            'race_id': 'count'
        })
        monthly['profit'] = monthly['return'] - monthly['bet_amount']
        monthly['roi'] = (monthly['return'] / monthly['bet_amount']) * 100
        
        print("\n=== Monthly Breakdown ===")
        print(monthly[['bet_amount', 'profit', 'roi', 'race_id']])

if __name__ == "__main__":
    # Example: Test with data from 2024-01-01
    start = date(2024, 1, 1)
    end = date(2025, 12, 31)
    
    # Or just a recent month for speed
    start = date(2025, 1, 1)
    
    backtester = Backtester(start, end)
    
    # Hack: Inject Bankroll update logic wrapper
    # Since we can't easily hook into the loop inside `run` without modifying `predict_race`,
    # We did modify `run` to update `self.inference_engine.kelly.bankroll`.
    # But wait, in `run` loop:
    #   1. Predict (uses kelly.bankroll)
    #   2. Place Bet (updates self.bankroll)
    #   3. Update kelly.bankroll = self.bankroll
    # This works!
    
    backtester.run()
