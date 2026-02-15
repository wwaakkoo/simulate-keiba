import asyncio
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import lightgbm as lgb
import numpy as np
import os

from app.api.schemas import PredictionResponse, PredictionItem
from app.predictor.sync_database import SessionLocal
from app.predictor.features import FeatureFactory
from app.models.race import Race

router = APIRouter(prefix="/races", tags=["predictions"])

# Load models globally
MODEL_LGB = None
MODEL_XGB = None

if os.path.exists('models/race_predictor_lgb.pkl'):
    try:
        MODEL_LGB = lgb.Booster(model_file='models/race_predictor_lgb.pkl')
        print("LGB model loaded")
    except Exception as e:
        print(f"Failed to load LGB model: {e}")

if os.path.exists('models/race_predictor_xgb.json'):
    try:
        import xgboost as xgb
        MODEL_XGB = xgb.XGBRanker()
        MODEL_XGB.load_model('models/race_predictor_xgb.json')
        print("XGB model loaded")
    except Exception as e:
        print(f"Failed to load XGB model: {e}")

# Fallback for v1
if not MODEL_LGB and os.path.exists('models/race_predictor_v1.pkl'):
    MODEL_LGB = lgb.Booster(model_file='models/race_predictor_v1.pkl')


def _predict_sync(race_id_str: str) -> dict:
    """Synchronous prediction logic to be run in executor"""
    if MODEL_LGB is None and MODEL_XGB is None:
        raise HTTPException(status_code=503, detail="No models loaded")
        
    db = SessionLocal()
    try:
        # Find PK from race_id string
        race = db.query(Race).filter(Race.race_id == race_id_str).first()
        if not race:
            raise HTTPException(status_code=404, detail=f"Race {race_id_str} not found")
        
        race_pk = race.id
        
        factory = FeatureFactory(db)
        try:
            result = factory.generate_features_for_race(race_pk)
        except ValueError as e:
             raise HTTPException(status_code=404, detail=str(e))
             
        if not result['features']:
            raise HTTPException(status_code=400, detail="Could not generate features for this race")
            
        X = np.array(result['features'])
        
        lgb_scores = MODEL_LGB.predict(X) if MODEL_LGB else np.zeros(len(X))
        xgb_scores = MODEL_XGB.predict(X) if MODEL_XGB else np.zeros(len(X))
        
        def normalize(scores):
            if np.max(scores) == np.min(scores): return scores
            return (scores - np.min(scores)) / (np.max(scores) - np.min(scores))
            
        # Weighted Ensemble (60% LGB, 40% XGB as a heuristic)
        # If one is missing, use the other 100%
        if MODEL_LGB and MODEL_XGB:
            predictions = 0.6 * normalize(lgb_scores) + 0.4 * normalize(xgb_scores)
            method = "ensemble_lgb_xgb"
        elif MODEL_LGB:
            predictions = lgb_scores
            method = "lightgbm_lambdarank"
        else:
            predictions = xgb_scores
            method = "xgboost_lambdarank"

        # Sort indices by score (descending for ranking)
        sorted_indices = np.argsort(-predictions)
        
        marks = ['◎', '○', '▲', '△']
        
        prediction_items = []
        
        # Create a mapping from index to rank/mark
        rank_map = {idx: i for i, idx in enumerate(sorted_indices)}
        
        for i in range(len(predictions)):
            # "i" is the original index in result['features']
            
            rank = rank_map[i] + 1
            mark = marks[rank_map[i]] if rank_map[i] < len(marks) else ""
            
            item = PredictionItem(
                horse_id=result['horse_ids'][i],
                horse_name=result['horse_names'][i],
                horse_number=result['horse_numbers'][i],
                predicted_position=float(predictions[i]),
                predicted_rank=rank,
                mark=mark
            )
            prediction_items.append(item)
            
        # Sort items by rank for cleaner response
        prediction_items.sort(key=lambda x: x.predicted_rank)
        
        return {
            "race_id": race_id_str,
            "predictions": prediction_items,
            "model_version": "v1-ensemble",
            "method": method
        }
        
    finally:
        db.close()

@router.post("/{race_id}/predict", response_model=PredictionResponse)
async def predict_race(race_id: str):
    """指定レースの着順をAIで予測する"""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, _predict_sync, race_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
