import os
import lightgbm as lgb
import numpy as np
from sklearn.metrics import mean_squared_error
from app.predictor.sync_database import SessionLocal
from app.predictor.features import FeatureFactory
from app.models.race import Race
from app.models.race_entry import RaceEntry

def train_model():
    """モデルの訓練を実行"""
    db = SessionLocal()
    factory = FeatureFactory(db)
    
    # 1. 全レースを時系列順に取得
    races = db.query(Race).order_by(Race.date).all()
    print(f"Total races: {len(races)}")
    
    if len(races) < 10:
        print("Not enough races to train. Need at least 10.")
        return None

    # 2. 時系列分割
    n = len(races)
    train_end = int(n * 0.8)
    valid_end = int(n * 0.9)
    
    train_races = races[:train_end]
    valid_races = races[train_end:valid_end]
    test_races = races[valid_end:]
    
    print(f"Train: {len(train_races)} races")
    print(f"Valid: {len(valid_races)} races")
    print(f"Test: {len(test_races)} races")
    
    # 3. 特徴量とラベルを生成
    def get_dataset(races_subset):
        X, y = [], []
        for race in races_subset:
            try:
                # Debug print for first few
                if len(X) < 5:
                    print(f"DEBUG: Race {race.id} has {len(race.entries)} entries")

                result = factory.generate_features_for_race(race.id)
                for features, horse_num in zip(result['features'], result['horse_numbers']):
                    # Match by horse_number (safer than name)
                    entry = next((e for e in race.entries if e.horse_number == horse_num), None)
                    
                    if entry and entry.finish_position is not None:
                        X.append(features)
                        y.append(float(entry.finish_position))
                    else:
                        pass # Entry missing or no finish pos
            except Exception as e:
                print(f"Error processing race {race.id}: {e}")
                continue
        return np.array(X), np.array(y)

    print("Generating Training Data...")
    X_train, y_train = get_dataset(train_races)
    print("Generating Validation Data...")
    X_valid, y_valid = get_dataset(valid_races)
    
    print(f"Training samples: {len(X_train)}")
    print(f"Validation samples: {len(X_valid)}")
    
    if len(X_train) == 0:
        print("No training samples found. Exiting.")
        return None

    # 4. LightGBM モデルの訓練
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': 0
    }
    
    train_data = lgb.Dataset(X_train, label=y_train, feature_name=FeatureFactory.get_feature_names())
    valid_data = lgb.Dataset(X_valid, label=y_valid, reference=train_data, feature_name=FeatureFactory.get_feature_names())
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=500,
        valid_sets=[train_data, valid_data],
        valid_names=['train', 'valid'],
        callbacks=[
            lgb.early_stopping(stopping_rounds=50),
            lgb.log_evaluation(period=50)
        ]
    )
    
    # 5. モデルの保存
    # Go up 3 levels from current file? No, current file is in app/predictor. 
    # Relative path "models" might be relative to CWD.
    # CWD when running "python -m app.predictor.trainer" is backend root.
    # So "models" folder in backend root? Or "backend/app/models"?
    # The user plan said "models/race_predictor_v1.pkl".
    # I'll save to "app/predictor/models" or just "models" in backend root.
    # Let's save to "models" in backend root for now as per user snippet implies.
    os.makedirs('models', exist_ok=True)
    model_path = 'models/race_predictor_v1.pkl'
    model.save_model(model_path)
    print(f"Model saved to {model_path}")
    
    # 6. 検証セットでの評価
    if len(X_valid) > 0:
        y_pred = model.predict(X_valid)
        rmse = np.sqrt(mean_squared_error(y_valid, y_pred))
        print(f"\nValidation RMSE: {rmse:.3f}")
    
    db.close()
    return model

if __name__ == "__main__":
    train_model()
