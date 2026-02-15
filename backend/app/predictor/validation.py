
import numpy as np
import pandas as pd
import lightgbm as lgb
from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple
from tqdm import tqdm

from app.models.race import Race
from app.predictor.features import FeatureFactory

class WalkForwardValidator:
    """
    時系列を考慮したWalk-Forward検証を行うクラス
    """
    def __init__(self, db: Session, initial_train_months: int = 24, test_months: int = 3, step_months: int = 3):
        self.db = db
        self.initial_train_months = initial_train_months
        self.test_months = test_months
        self.step_months = step_months
        self.factory = FeatureFactory(db)
        self.feature_names = FeatureFactory.get_feature_names()

    def get_all_races(self) -> List[Race]:
        return self.db.query(Race).order_by(Race.date).all()

    def split_time_series(self, df_races: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        時系列順に分割設定を生成
        df_races: ['race_id', 'date'] を持つDataFrame
        """
        splits = []
        min_date = df_races['date'].min()
        max_date = df_races['date'].max()
        
        # Start training end date
        current_train_end = min_date + relativedelta(months=self.initial_train_months)
        
        while current_train_end + relativedelta(months=self.test_months) <= max_date:
            train_start = min_date # Expanding window (or use rolling window by setting start)
            # train_start = current_train_end - relativedelta(months=self.initial_train_months) # Rolling Window
            
            test_start = current_train_end
            test_end = test_start + relativedelta(months=self.test_months)
            
            # Filter Races
            train_mask = (df_races['date'] >= train_start) & (df_races['date'] < current_train_end)
            test_mask = (df_races['date'] >= test_start) & (df_races['date'] < test_end)
            
            if train_mask.sum() > 0 and test_mask.sum() > 0:
                splits.append({
                    'train_idx': df_races[train_mask].index,
                    'test_idx': df_races[test_mask].index,
                    'train_period': f"{train_start} ~ {current_train_end}",
                    'test_period': f"{test_start} ~ {test_end}",
                    'train_races': df_races.loc[train_mask, 'race_id'].tolist(),
                    'test_races': df_races.loc[test_mask, 'race_id'].tolist()
                })
            
            # Slide
            current_train_end += relativedelta(months=self.step_months)
            
        return splits

    def prepare_data(self, race_ids: List[str]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        リストされたRace IDに対して特徴量とラベルを生成
        """
        # Note: This might be slow. Optimization: Batch load or caching.
        # reusing logic from trainer.py
        X, y, groups = [], [], []
        
        # Pre-fetch races to avoid lazy loading issues
        # races = self.db.query(Race).filter(Race.race_id.in_(race_ids)).all()
        # The above in_ might fail for large lists (sqlite limit).
        # Should iterate and fetch? Or better Pass Race Objects.
        
        # Let's assume we pass Race IDs, valid logic:
        # Actually FeatureFactory needs race_id (int PK or string ID?)
        # FeatureFactory.generate_features_for_race takes race_id (int PK).
        # Trainer logic uses Race objects.
        # Let's verify trainer.py usage: factory.generate_features_for_race(race.id) -> PK.
        
        # So inputs race_ids should be PKs.
        pass
        
    def prepare_dataset_for_races(self, races: List[Race]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[Dict]]:
        """
        レースオブジェクトのリストからデータセットを作成
        Returns: X, y, groups, metadata(race_id, horse_id etc for evaluation)
        """
        X, y, groups = [], [], []
        metadata = [] # To verify results (roi calc)
        race_data = {}
        
        print(f"Preparing data for {len(races)} races...")
        for race in tqdm(races, leave=False):
            try:
                result = self.factory.generate_features_for_race(race.id)
                
                # Retrieve RaceEntry directly to get label
                entries = race.entries
                entry_map = {e.horse_number: e for e in entries}
                
                race_X, race_y = [], []
                race_meta = []
                
                features_list = result['features']
                horse_numbers = result['horse_numbers']
                horse_ids = result['horse_ids']
                
                for i, feats in enumerate(features_list):
                    h_num = horse_numbers[i]
                    entry = entry_map.get(h_num)
                    
                    if entry and entry.finish_position is not None:
                        # Label: Relevance (20 - Rank)
                        relevance = max(0, 20 - entry.finish_position) # Or just 1 if rank=1? LambdaRank needs relevance.
                        
                        race_X.append(feats)
                        race_y.append(relevance)
                        
                        race_meta.append({
                            'race_id': race.race_id,
                            'horse_id': horse_ids[i],
                            'horse_number': h_num,
                            'rank': entry.finish_position,
                            'odds': entry.odds if entry.odds is not None else np.nan,
                            'horse_name': entry.horse.name if entry.horse else ""
                        })
                

                
                if race_X:
                    race_data[race.id] = (race_X, race_y, race_meta) # Use PK as key
                    
            except Exception as e:
                # print(f"Error: {e}")
                continue
        
        self.race_data_cache = race_data
        return race_data

    def get_data_from_cache(self, race_ids: List[str]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[Dict]]:
        X, y, groups = [], [], []
        metadata = []
        
        for rid in race_ids:
            if rid in self.race_data_cache:
                rX, rY, rMeta = self.race_data_cache[rid]
                X.extend(rX)
                y.extend(rY)
                groups.append(len(rX))
                metadata.extend(rMeta)
        
        return np.array(X), np.array(y), np.array(groups), metadata

    def train_model(self, X, y, groups):
        train_data = lgb.Dataset(X, label=y, group=groups, feature_name=self.feature_names)
        
        params = {
            'objective': 'lambdarank',
            'metric': 'ndcg',
            'ndcg_eval_at': [1, 3, 5],
            'learning_rate': 0.05,
            'num_leaves': 31,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1
        }
        
        # Valid set same as train for simplicity in Walk-Forward (or split internal?)
        # Usually we just train on Train and test on Test. 
        # But we need num_rounds. Use standard 100-500.
        
        model = lgb.train(
            params,
            train_data,
            num_boost_round=100, # Faster for validation
            valid_sets=[train_data],
            callbacks=[lgb.log_evaluation(0)] # Silent
        )
        return model

    def evaluate(self, model, X, metadata):
        # Predict
        preds = model.predict(X)
        
        # Organize by Race
        # metadata contains list of entries corresponding to X rows.
        # We need to reconstruct races.
        
        df = pd.DataFrame(metadata)
        df['score'] = preds
        
        # Calc Metrics
        total_roi = 0
        total_bets = 0
        hits = 0
        
        # Simple strategy for evaluation: Bet Top 1
        # (We can apply Kelly here too if we want, but Top 1 ROI is a good baseline)
        
        races = df.groupby('race_id')
        investment = 0
        return_amount = 0
        
        for race_id, group in races:
            # Sort by Score Desc
            top1 = group.sort_values('score', ascending=False).iloc[0]
            
            # Bet ¥100 if odds exist
            odds = top1['odds']
            if pd.isna(odds):
                continue

            bet = 100
            investment += bet
            total_bets += 1
            
            if top1['rank'] == 1:
                hits += 1
                return_amount += bet * odds
        
        win_rate = hits / total_bets if total_bets > 0 else 0
        roi = (return_amount - investment) / investment if investment > 0 else 0
        
        return {
            'win_rate': win_rate,
            'roi': roi,
            'bets': total_bets,
            'profit': return_amount - investment
        }

    def run(self):
        races = self.get_all_races()
        df_races = pd.DataFrame([{
            'race_id': r.id, # PK
            'race_id_str': r.race_id,
            'date': r.date
        } for r in races])
        
        
        # Precompute all data
        print("Precomputing features for all races...")
        self.prepare_dataset_for_races(races) # Populates self.race_data_cache
        
        splits = self.split_time_series(df_races)
        print(f"Starting Walk-Forward Validation with {len(splits)} folds...")
        
        results = []
        for i, split in enumerate(splits):
            print(f"\n=== Fold {i+1}/{len(splits)} ===")
            print(f"Train: {split['train_period']}")
            print(f"Test:  {split['test_period']}")
            
            train_pks = split['train_races']
            test_pks = split['test_races']
            
            # Fetch from Cache
            X_train, y_train, g_train, _ = self.get_data_from_cache(train_pks)
            X_test, _, _, meta_test = self.get_data_from_cache(test_pks)
            
            if len(X_train) == 0 or len(X_test) == 0:
                print("Skipping fold due to empty data.")
                continue
                
            # Train
            model = self.train_model(X_train, y_train, g_train)
            
            # Evaluate
            metrics = self.evaluate(model, X_test, meta_test)
            
            print(f"Validation Results: Win Rate={metrics['win_rate']:.1%}, ROI={metrics['roi']:.1%}, Bets={metrics['bets']}")
            
            results.append({
                'fold': i+1,
                'period': split['test_period'],
                **metrics
            })
            
        return pd.DataFrame(results)
