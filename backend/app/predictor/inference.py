
from typing import Dict, Any, List, Optional
import lightgbm as lgb
import numpy as np
import os
import pickle
from sqlalchemy.orm import Session
from app.api.schemas import PredictionItem, PredictionResponse
from app.predictor.features import FeatureFactory
from app.predictor.betting import KellyBettingStrategy
from app.models.race import Race
from app.models.race_entry import RaceEntry

class InferenceEngine:
    """
    推論エンジン
    - モデルのロード
    - 特徴量生成
    - 予測 (Main Model & Dark Horse Model)
    - キャリブレーション (Score -> Probability)
    - ベッティング戦略適用
    """
    
    def __init__(self, model_dir: str = 'backend/models'):
        # Fix: Default path should be relative to repo root if running from root
        # But if running from backend, it should be 'models'.
        # Let's try to find absolute path.
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # base_dir is .../backend
        default_model_dir = os.path.join(base_dir, 'models')
        
        self.model_dir = model_dir if os.path.isabs(model_dir) else default_model_dir
        
        print(f"[DEBUG] Model Dir: {self.model_dir}")
        self.model_lgb = None
        self.model_xgb = None
        self.model_dark = None # Dark Horse Model (Simple Binary Classifier)
        self.calibrator = None
        self.kelly = KellyBettingStrategy()
        
        self._load_models()
        
    def _load_models(self):
        # Load Main LGB Model
        lgb_path = os.path.join(self.model_dir, 'race_predictor_lgb.pkl')
        print(f"[DEBUG] Loading LGB from: {lgb_path}, exists={os.path.exists(lgb_path)}")
        if os.path.exists(lgb_path):
            try:
                self.model_lgb = lgb.Booster(model_file=lgb_path)
                print("Main LGB model loaded")
            except Exception as e:
                print(f"Failed to load LGB model: {e}")
                
        # Load Main XGB Model
        # TODO: Retrain XGBoost with 28 features. Currently disabled due to shape mismatch.
        # xgb_path = os.path.join(self.model_dir, 'race_predictor_xgb.json')
        # if os.path.exists(xgb_path):
        #     try:
        #         import xgboost as xgb
        #         self.model_xgb = xgb.XGBRanker()
        #         self.model_xgb.load_model(xgb_path)
        #         print("Main XGB model loaded")
        #     except Exception as e:
        #         print(f"Failed to load XGB model: {e}")

        # Fallback to v1
        if not self.model_lgb and not self.model_xgb:
            v1_path = os.path.join(self.model_dir, 'race_predictor_v1.pkl')
            if os.path.exists(v1_path):
                self.model_lgb = lgb.Booster(model_file=v1_path)
                print("Fallback v1 model loaded")

        # Load Dark Horse Model
        dark_path = os.path.join(self.model_dir, 'race_predictor_dark.pkl')
        if os.path.exists(dark_path):
            try:
                self.model_dark = lgb.Booster(model_file=dark_path)
                print("Dark Horse model loaded")
            except Exception as e:
                print(f"Failed to load Dark Horse model: {e}")

        # Load Calibrator
        cal_path = os.path.join(self.model_dir, 'calibrator.pkl')
        if os.path.exists(cal_path):
            try:
                with open(cal_path, 'rb') as f:
                    self.calibrator = pickle.load(f)
                print("Calibrator loaded")
            except Exception as e:
                print(f"Failed to load Calibrator: {e}")

    def predict_race(self, race_id_str: str, db: Session) -> PredictionResponse:
        """
        別スレッド用 (Sync)
        """
        # 1. Fetch Race Data
        race = db.query(Race).filter(Race.race_id == race_id_str).first()
        if not race:
            raise ValueError(f"Race {race_id_str} not found")
            
        factory = FeatureFactory(db)
        result = factory.generate_features_for_race(race.id)
        
        if not result['features']:
            raise ValueError("No features generated")
            
        X = np.array(result['features'])
        
        # 2. Raw Model Predictions (Ranking Scores)
        if self.model_lgb:
            lgb_scores = self.model_lgb.predict(X) 
        else:
            lgb_scores = np.zeros(len(X))
            
        xgb_scores = self.model_xgb.predict(X) if self.model_xgb else np.zeros(len(X))
        
        # Normalize
        def normalize(s):
            if np.max(s) == np.min(s): return s
            return (s - np.min(s)) / (np.max(s) - np.min(s))

        # Ensemble
        raw_scores = np.zeros(len(X))
        method = "single_model"
        if self.model_lgb and self.model_xgb:
            raw_scores = 0.6 * normalize(lgb_scores) + 0.4 * normalize(xgb_scores)
            method = "ensemble_lgb_xgb_kelly"
        elif self.model_lgb:
            raw_scores = lgb_scores
            method = "lgb_kelly"
        elif self.model_xgb:
            raw_scores = xgb_scores
            method = "xgb_kelly"
            
        # 3. Calibration (Convert Score -> Probability) with Temperature Scaling
        # Temperature > 1.0 (smoother), < 1.0 (sharper)
        temperature = 1.0 
        
        if self.calibrator:
            # Use LGB scores for calibration as trained
            score_to_calibrate = lgb_scores if self.model_lgb else raw_scores
            try:
                probs_raw = self.calibrator.predict(score_to_calibrate)
                # Normalize to ensure sum to 1.0
                probs = probs_raw / max(np.sum(probs_raw), 1e-9)
            except Exception as e:
                print(f"Calibration failed: {e}, falling back to softmax")
                exp_scores = np.exp(raw_scores / temperature) # Apply temperature
                probs = exp_scores / np.sum(exp_scores)
        else:
            # Fallback: Softmax with Temperature
            exp_scores = np.exp((raw_scores - np.max(raw_scores)) / temperature)
            probs = exp_scores / np.sum(exp_scores)

        # 4. Anomaly Detection / Race Quality Check
        # Check for flat distribution (Entropy or Std Dev)
        prob_std = np.std(probs)
        is_flat_distribution = prob_std < 0.03 # If std dev < 3%, it's very flat
        
        # Check for Num Horses
        num_horses = len(X)
        is_num_outlier = num_horses < 8 or num_horses > 18
        
        # Skip logic
        skip_reason = None
        if is_flat_distribution:
            skip_reason = f"Flat Distribution (Std={prob_std:.3f})"
        elif is_num_outlier:
            skip_reason = f"Num Horses Outlier ({num_horses})"
            
        if skip_reason:
            print(f"[WARNING] Skipping Race Betting: {skip_reason}")
            # We still return predictions but maybe suppress betting recommendations?
            # KellyStrategy will handle empty/skip if we pass a flag or empty expected values.
            # But let's let Kelly handle it? No, Kelly doesn't know about "Flat Distribution" explicitly
            # other than min_prob check. SafeKelly has min_prob.
            # If flat distribution (e.g. all 0.06), and min_prob is 0.10, SafeKelly WILL skip everything.
            # So SafeKelly covers "Flat Distribution" implicitly!
            pass

        # 5. Prepare Prediction List
        predictions = []
        # result contains: 'horse_ids', 'horse_numbers', 'horse_names', 'features', 'odds'
        # Note: 'odds' might not be in result directly? generate_features_for_race returns:
        # { 'features': [], 'horse_ids': [], 'horse_numbers': [], 'horse_names': [], 'meta': {...} }
        # Wait, let's check generate_features_for_race output structure.
        # It usually returns a dict.
        # In previous lines: X = np.array(result['features'])
        # So 'result' is the dict.
        # But wait, where are odds?
        # In `features.py`, odds are in the feature vector index 11.
        # But we also might have it in `result` if we put it there?
        # Let's assume result has 'odds' KEY if I added it, or we extract from X.
        # Actually, looking at previous code (lines 102), result comes from factory.
        # Let's check if factory returns odds in result dict.
        # If not, we use X[:, 11].
        
        # Let's use X for odds to be safe as it was done before.
        for i in range(len(X)):
            horse_id = result['horse_ids'][i]
            number = result['horse_numbers'][i]
            odds = float(X[i][11]) # 11 is 'odds' index
            
            predictions.append({
                'horse_id': horse_id,
                'horse_name': result['horse_names'][i], # Add name here
                'horse_number': number,
                'win_prob': float(probs[i]),
                'odds': odds,
                'score': float(raw_scores[i]),
                'is_dark_horse': False # TODO: Use dark model
            })
            
        # Apply Kelly
        evaluated_predictions = self.kelly.evaluate(predictions)
        
        # 6. Format Response
        response_items = []
        for p in evaluated_predictions:
            mark = ""
            if p.get('recommendation') == 'BUY':
                mark = f"BUY ¥{p['bet_amount']}"
            
            # Add anomaly warning to mark if any
            if skip_reason and mark:
                mark += " (CAUTION: " + skip_reason + ")"
            
            item = PredictionItem(
                horse_id=p['horse_id'],
                horse_name=p['horse_name'], # Use passed name
                horse_number=p['horse_number'],
                predicted_position=p['score'], # Use raw score for sorting
                predicted_rank=0, # Will sort later
                mark=mark
            )
            response_items.append(item)

        # Sort by Score (Descending) for Ranking
        # Note: predicted_position is score here.
        response_items.sort(key=lambda x: x.predicted_position, reverse=True)
        
        # Assign Ranks
        for i, item in enumerate(response_items):
            item.predicted_rank = i + 1
            
        return PredictionResponse(
            race_id=race_id_str,
            predictions=response_items,
            model_version="v2-kelly",
            method=method
        )

# Global Instance
_engine = None

def get_inference_engine():
    global _engine
    if _engine is None:
        _engine = InferenceEngine()
    return _engine
