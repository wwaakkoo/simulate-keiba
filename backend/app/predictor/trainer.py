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
        X, y, groups = [], [], []
        for race in races_subset:
            race_X, race_y = [], []
            try:
                result = factory.generate_features_for_race(race.id)
                for features, horse_num in zip(result['features'], result['horse_numbers']):
                    # Match by horse_number
                    entry = next((e for e in race.entries if e.horse_number == horse_num), None)
                    
                    if entry and entry.finish_position is not None:
                        race_X.append(features)
                        # LambdaRank assumes higher is better, so 1st place should have highest value
                        # Using 20 - position as a simple relevance score
                        relevance = max(0, 20 - entry.finish_position)
                        race_y.append(relevance)
                
                if race_X:
                    X.extend(race_X)
                    y.extend(race_y)
                    groups.append(len(race_X))
            except Exception as e:
                print(f"Error processing race {race.id}: {e}")
                continue
        return np.array(X), np.array(y), np.array(groups)

    print("Generating Training Data...")
    X_train, y_train, groups_train = get_dataset(train_races)
    print("Generating Validation Data...")
    X_valid, y_valid, groups_valid = get_dataset(valid_races)
    
    print(f"Training samples: {len(X_train)} ({len(groups_train)} races)")
    print(f"Validation samples: {len(X_valid)} ({len(groups_valid)} races)")
    
    if len(X_train) == 0:
        print("No training samples found. Exiting.")
        return None

    # 4. LightGBM モデルの訓練 (Ranking)
    params_lgb = {
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
    
    lgb_train = lgb.Dataset(X_train, label=y_train, group=groups_train, feature_name=FeatureFactory.get_feature_names())
    lgb_valid = lgb.Dataset(X_valid, label=y_valid, group=groups_valid, reference=lgb_train, feature_name=FeatureFactory.get_feature_names())
    
    print("\nTraining LightGBM Ranker...")
    lgb_model = lgb.train(
        params_lgb,
        lgb_train,
        num_boost_round=1000,
        valid_sets=[lgb_train, lgb_valid],
        valid_names=['train', 'valid'],
        callbacks=[lgb.early_stopping(stopping_rounds=100), lgb.log_evaluation(period=100)]
    )

    # 4b. XGBoost モデルの訓練 (Ranking)
    print("\nTraining XGBoost Ranker...")
    import xgboost as xgb
    
    # XGBoost uses qid or group. Using qid is recommended for newer versions.
    # We need to construct qids from groups
    def groups_to_qid(groups):
        qid = []
        for i, g in enumerate(groups):
            qid.extend([i] * g)
        return np.array(qid)
    
    qid_train = groups_to_qid(groups_train)
    qid_valid = groups_to_qid(groups_valid)
    
    xgb_model = xgb.XGBRanker(
        objective='rank:ndcg',
        lambdarank_pair_method='topk',
        learning_rate=0.05,
        n_estimators=1000,
        max_depth=6,
        importance_type='gain',
        multi_strategy='one_output_per_tree',
        early_stopping_rounds=100
    )
    
    xgb_model.fit(
        X_train, y_train,
        qid=qid_train,
        eval_set=[(X_valid, y_valid)],
        eval_qid=[qid_valid],
        verbose=100
    )
    
    # 5. モデルの保存
    os.makedirs('models', exist_ok=True)
    lgb_model.save_model('models/race_predictor_lgb.pkl')
    xgb_model.save_model('models/race_predictor_xgb.json')
    
    # Also save as the default v1 (for now let's use LightGBM as primary or a wrapper)
    # The API currently loads as lgb.Booster.
    # To support ensemble in API, we'll need to change predict.py.
    # For now, let's keep LightGBM as v1 for compatibility while we test ensemble.
    lgb_model.save_model('models/race_predictor_v1.pkl')
    print(f"Models saved in models/ directory")
    
    # 6. Ensemble Evaluation
    if len(X_valid) > 0:
        lgb_pred = lgb_model.predict(X_valid)
        xgb_pred = xgb_model.predict(X_valid)
        
        # Normalize scores for ensemble (simple min-max)
        def normalize(scores):
            return (scores - np.min(scores)) / (np.max(scores) - np.min(scores)) if np.max(scores) != np.min(scores) else scores
            
        ensemble_pred = 0.6 * normalize(lgb_pred) + 0.4 * normalize(xgb_pred)
        print("\nEnsemble evaluation complete.")
    
    db.close()
    return lgb_model

if __name__ == "__main__":
    train_model()
