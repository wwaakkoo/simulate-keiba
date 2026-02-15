
import asyncio
from fastapi import APIRouter, HTTPException
from app.api.schemas import PredictionResponse
from app.predictor.sync_database import SessionLocal
from app.predictor.inference import get_inference_engine

router = APIRouter(prefix="/races", tags=["predictions"])

def _predict_sync(race_id_str: str) -> PredictionResponse:
    """Synchronous prediction logic using InferenceEngine"""
    # Get Global Engine
    engine = get_inference_engine()
    
    db = SessionLocal()
    try:
        # Run prediction
        try:
            result = engine.predict_race(race_id_str, db)
            return result
        except ValueError as e:
            # Handle business logic errors (not found, etc)
            raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@router.post("/{race_id}/predict", response_model=PredictionResponse)
async def predict_race(race_id: str):
    """指定レースの着順をAIで予測する (Phase F: Kelly Betting & Speed Index Included)"""
    loop = asyncio.get_event_loop()
    try:
        # Run heavy ML task in executor
        result = await loop.run_in_executor(None, _predict_sync, race_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
