import sys
import os
from sqlalchemy import select

from app.models.race import Race
from app.predictor.features import FeatureFactory

# Add backend to path
sys.path.append(os.getcwd())

async def test_features():
    # Use sync session for FeatureFactory as it currently seems to use synchronous sqlalchemy session in the code I read?
    # Wait, features.py imports `sqlalchemy.orm.Session`.
    # But database.py provides `AsyncSession`.
    # `trainer.py` imports `from app.predictor.sync_database import SessionLocal`.
    # Let's check `sync_database.py`.
    pass

if __name__ == "__main__":
    from app.predictor.sync_database import SessionLocal
    
    db = SessionLocal()
    factory = FeatureFactory(db)
    
    # Get a recent race (which should have full data)
    # And an old race (repaired)
    
    recent_race = db.query(Race).filter(Race.date >= '2024-01-01').first()
    repaired_race = db.query(Race).filter(Race.race_id == '201804020411').first()
    
    print(f"Recent race found: {recent_race is not None}")
    print(f"Repaired race found: {repaired_race is not None}")
    
    races_to_test = [r for r in [recent_race, repaired_race] if r]
    
    print(f"Testing feature generation for {len(races_to_test)} races...")
    
    for race in races_to_test:
        print(f"\n--- Race: {race.name} ({race.race_id}) ---")
        print(f"Date: {race.date}, Venue: {race.venue}, Course: {race.course_type}")
        
        try:
            result = factory.generate_features_for_race(race.id)
            features_list = result['features']
            names = result['horse_names']
            
            print(f"Successfully generated features for {len(features_list)} horses.")
            
            # Print first horse's features
            if features_list:
                print("First horse features:")
                feat_names = FeatureFactory.get_feature_names()
                for name, value in zip(feat_names, features_list[0]):
                    print(f"  {name}: {value}")
                    
        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()

    db.close()
