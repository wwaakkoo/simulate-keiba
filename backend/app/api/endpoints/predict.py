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

# Load model globally
MODEL_PATH = 'models/race_predictor_v1.pkl'
MODEL = None

if os.path.exists(MODEL_PATH):
    try:
        MODEL = lgb.Booster(model_file=MODEL_PATH)
        print(f"Model loaded from {MODEL_PATH}")
    except Exception as e:
        print(f"Failed to load model: {e}")

def _predict_sync(race_id_str: str) -> dict:
    """Synchronous prediction logic to be run in executor"""
    if MODEL is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
        
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
        predictions = MODEL.predict(X)
        
        # Sort indices by predicted position (asc)
        sorted_indices = np.argsort(predictions)
        
        marks = ['◎', '○', '▲', '△']
        
        prediction_items = []
        
        # We need to map sorted indices back to original indices to build the response list.
        # However, the user wants a list of predictions for each horse.
        # Better to return a list where order doesn't matter (client can match by horse_number) 
        # OR return sorted list. The schema has `predicted_rank`.
        
        # Create a mapping from index to rank/mark
        rank_map = {idx: i for i, idx in enumerate(sorted_indices)}
        
        for i in range(len(predictions)):
            # "i" is the original index in result['features'] and result['horse_names']
            
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
            "model_version": "v1",
            "method": "lightgbm_regression_mvp"
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
