import sys
import os
import asyncio
import numpy as np
import lightgbm as lgb
from app.predictor.sync_database import SessionLocal
from app.predictor.features import FeatureFactory
from app.models.race import Race
from app.api.endpoints.predict import _predict_sync

# Add backend to path
sys.path.append(os.getcwd())

def test_prediction_logic():
    print("Testing prediction logic...")
    
    # Check model existence
    model_path = 'models/race_predictor_v1.pkl'
    if not os.path.exists(model_path):
        print("Model file not found!")
        return

    # Mocking the global MODEL in predict.py is hard from here without importing it.
    # But _predict_sync uses the global MODEL variable in app.api.endpoints.predict.
    # So if I import it, I might need to initialize it.
    
    from app.api.endpoints import predict
    
    if predict.MODEL is None:
        print("Loading model...")
        predict.MODEL = lgb.Booster(model_file=model_path)
    
    # Use a known race ID
    race_id = "202406010111" # Nakayama Kim Pai
    
    try:
        result = predict._predict_sync(race_id)
        print("Prediction success!")
        print(f"Race ID: {result['race_id']}")
        print(f"Model Version: {result['model_version']}")
        print(f"Predictions: {len(result['predictions'])}")
        
        for item in result['predictions']:
            print(f"Rank {item.predicted_rank} ({item.mark}): {item.horse_name} (ID: {item.horse_id}) - Score: {item.predicted_position:.4f}")
            
    except Exception as e:
        print(f"Prediction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_prediction_logic()
