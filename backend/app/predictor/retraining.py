
import os
import lightgbm as lgb
import pandas as pd
import numpy as np
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.race import Race
from app.predictor.features import FeatureFactory

class IncrementalRetrainer:
    """
    定期的なモデル再学習を行うクラス
    Concept Driftに対応するため、直近のデータを重視(Time Decay)して学習する。
    """
    def __init__(self, db: Session, model_dir: str = "models/incremental"):
        self.db = db
        self.model_dir = model_dir
        self.factory = FeatureFactory(db)
        self.feature_names = FeatureFactory.get_feature_names()
        
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

    def _calculate_sample_weights(self, dates: pd.Series, reference_date: date, half_life_days: int = 90) -> np.ndarray:
        """
        時間減衰重みを計算
        reference_dateに近いほど重みが大きく(1.0)、遠いほど小さくなる。
        half_life_days: 重みが半分になる日数
        """
        # Date difference in days
        # Ensure dates are date objects
        # Input might be datetime or date.
        
        ref_ts = pd.Timestamp(reference_date)
        days_old = (ref_ts - pd.to_datetime(dates)).dt.days
        
        # Avoid negative days (future data?) -> Should not happen in training
        days_old = np.maximum(days_old, 0)
        
        # Weight = exp(-ln(2) * days / half_life)
        weights = np.exp(-np.log(2) * days_old / half_life_days)
        
        return weights.values

    def train_for_date(self, current_date: date, lookback_months: int = 24) -> Optional[lgb.Booster]:
        """
        指定された日付時点でのモデルを学習する
        """
        start_date = current_date - relativedelta(months=lookback_months)
        
        print(f"Retraining model for {current_date} (Data: {start_date} ~ {current_date})")
        
        # 1. Fetch Races
        races = self.db.query(Race).filter(
            Race.date >= start_date,
            Race.date < current_date
        ).order_by(Race.date).all()
        
        if len(races) < 50:
            print("Not enough races to retrain.")
            return None
            
        # 2. Prepare Data
        # Re-using logic? Or use validation's logic?
        # Ideally we share the data preparation logic.
        # But for now, let's implement efficient batch loading if possible, or iterate.
        # Using a simplified version of validation's logic tailored for retraining.
        
        X, y, groups = [], [], []
        dates = []
        
        # TODO: Optimization - Batch fetching Features?
        # For now, iterate (simpler to implement)
        
        for race in races:
            try:
                result = self.factory.generate_features_for_race(race.id)
                entries = race.entries
                entry_map = {e.horse_number: e for e in entries}
                
                race_X, race_y = [], []
                
                for i, feats in enumerate(result['features']):
                    h_num = result['horse_numbers'][i]
                    entry = entry_map.get(h_num)
                    if entry and entry.finish_position is not None:
                        race_X.append(feats)
                        relevance = max(0, 20 - entry.finish_position)
                        race_y.append(relevance)
                
                if race_X:
                    X.extend(race_X)
                    y.extend(race_y)
                    groups.append(len(race_X))
                    dates.extend([race.date] * len(race_X))
                    
            except Exception as e:
                continue
        
        if not X:
            return None
            
        X = np.array(X)
        y = np.array(y)
        groups = np.array(groups)
        dates_series = pd.Series(dates)
        
        # 3. Calculate Weights
        weights = self._calculate_sample_weights(dates_series, current_date)
        
        # 4. Train
        train_data = lgb.Dataset(
            X, label=y, group=groups, weight=weights,
            feature_name=self.feature_names
        )
        
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
        
        model = lgb.train(
            params,
            train_data,
            num_boost_round=500
        )
        
        # 5. Save Model
        model_filename = f"model_{current_date.strftime('%Y%m%d')}.txt"
        save_path = os.path.join(self.model_dir, model_filename)
        model.save_model(save_path)
        print(f"Model saved to {save_path}")
        
        return model
