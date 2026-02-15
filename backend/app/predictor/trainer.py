
import os
import lightgbm as lgb
import numpy as np
import pickle
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import KFold
from app.predictor.sync_database import SessionLocal
from app.predictor.features import FeatureFactory
from app.models.race import Race

def train_model():
    """モデルの訓練を実行 (Phase F: Dark Horse & Calibration Included)"""
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
    
    # 3. 特徴量とラベルを生成
    # We need to collect "Dark Horse" label as well: (Popularity >= 4 AND Rank <= 3)
    def get_dataset(races_subset):
        X, y, groups = [], [], []
        y_dark = [] # Binary label for Dark Horse
        
        for race in races_subset:
            race_X, race_y, race_y_dark = [], [], []
            try:
                result = factory.generate_features_for_race(race.id)
                sorted_entries = sorted(race.entries, key=lambda x: float(x.odds) if x.odds else 0.0)
                
                # Popularity Map (by odds)
                pop_map = {e.horse_id: i+1 for i, e in enumerate(sorted_entries)}
                
                for features, horse_num, horse_id in zip(result['features'], result['horse_numbers'], result['horse_ids']):
                    entry = next((e for e in race.entries if e.horse_number == horse_num), None)
                    
                    if entry and entry.finish_position is not None:
                        race_X.append(features)
                        
                        # Main Label: Relevance
                        relevance = max(0, 20 - entry.finish_position)
                        race_y.append(relevance)
                        
                        # Dark Horse Label
                        pop = pop_map.get(horse_id, 1)
                        is_dark = 1 if (pop >= 4 and entry.finish_position <= 3) else 0
                        race_y_dark.append(is_dark)
                
                if race_X:
                    X.extend(race_X)
                    y.extend(race_y)
                    y_dark.extend(race_y_dark)
                    groups.append(len(race_X))
            except Exception as e:
                # print(f"Error processing race {race.id}: {e}")
                continue
        return np.array(X), np.array(y), np.array(groups), np.array(y_dark)

    print("Generating Training Data...")
    X_train, y_train, groups_train, y_dark_train = get_dataset(train_races)
    print("Generating Validation Data...")
    X_valid, y_valid, groups_valid, y_dark_valid = get_dataset(valid_races)
    
    print(f"Training samples: {len(X_train)} ({len(groups_train)} races)")
    
    if len(X_train) == 0:
        print("No training samples found. Exiting.")
        return None

    # 4. LightGBM モデルの訓練 (Ranking)
    # ... (Same as before)
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
    
    # 5. XGBoost (Skipping for brevity in this step, focusing on Calibration/DarkHorse)
    # You can uncomment or re-add XGBoost part if needed for ensemble.
    
    # 6. Probability Calibration (Isotonic Regression)
    print("\nTraining Calibrator (Isotonic Regression)...")
    # Use Out-of-Fold predictions to avoid overfitting
    # Since we have groups (queries), we should use GroupKFold, but simple KFold is okay if we shuffle?
    # Actually, for ranking, we calculate score.
    # We want P(Win | Score).
    # Simple KFold on races.
    
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    oof_preds = np.zeros(len(X_train))
    
    # We need to split BY RACE (groups), not by sample, to prevent leakage within a race.
    # Manually split groups
    group_indices = np.cumsum([0] + list(groups_train))
    n_races = len(groups_train)
    
    # Map back to X indices
    race_indices = np.arange(n_races)
    
    for fold, (tr_race_idx, val_race_idx) in enumerate(kf.split(race_indices)):
        # Construct X_tr, y_tr
        tr_indices = []
        for ri in tr_race_idx:
            start = group_indices[ri]
            end = group_indices[ri+1]
            tr_indices.extend(range(start, end))
            
        val_indices = []
        for ri in val_race_idx:
            start = group_indices[ri]
            end = group_indices[ri+1]
            val_indices.extend(range(start, end))
            
        X_tr_fold = X_train[tr_indices]
        y_tr_fold = y_train[tr_indices]
        g_tr_fold = groups_train[tr_race_idx]
        
        X_val_fold = X_train[val_indices]
        
        # Train fold model
        d_tr = lgb.Dataset(X_tr_fold, label=y_tr_fold, group=g_tr_fold)
        m_fold = lgb.train(params_lgb, d_tr, num_boost_round=100)
        
        # Predict fold valid
        oof_preds[val_indices] = m_fold.predict(X_val_fold)
        
    # Fit Isotonic Regression on OOF preds
    # Target: 1 if 1st place (relevance=20 implies 1st place since 20-1=19, wait. Logic was 20-pos.)
    # Entry.finish_position == 1 -> relevance = 19
    # Let's check logic: max(0, 20 - entry.finish_position). If pos=1, val=19.
    # Convert y_train to binary (1st place)
    # y_train contains relevance scores.
    # finish_position = 20 - relevance roughly.
    y_binary = (y_train == 19).astype(int) 
    
    calibrator = IsotonicRegression(out_of_bounds='clip')
    calibrator.fit(oof_preds, y_binary)
    print("Calibrator trained.")

    # 7. Dark Horse Model (Binary Classification)
    print("\nTraining Dark Horse Model...")
    # Parameters for imbalanced classification
    params_dark = {
        'objective': 'binary',
        'metric': 'auc',
        'is_unbalance': True, # Important for hole horses
        'learning_rate': 0.05,
        'num_leaves': 31,
        'verbose': -1
    }
    
    lgb_train_dark = lgb.Dataset(X_train, label=y_dark_train, feature_name=FeatureFactory.get_feature_names())
    lgb_valid_dark = lgb.Dataset(X_valid, label=y_dark_valid, reference=lgb_train_dark, feature_name=FeatureFactory.get_feature_names())
    
    dark_model = lgb.train(
        params_dark,
        lgb_train_dark,
        num_boost_round=1000,
        valid_sets=[lgb_train_dark, lgb_valid_dark],
        callbacks=[lgb.early_stopping(stopping_rounds=100), lgb.log_evaluation(period=100)]
    )

    # 8. Save Models
    os.makedirs('models', exist_ok=True)
    lgb_model.save_model('models/race_predictor_lgb.pkl')
    dark_model.save_model('models/race_predictor_dark.pkl')
    
    with open('models/calibrator.pkl', 'wb') as f:
        pickle.dump(calibrator, f)
        
    print("All models saved successfully.")
    
    db.close()

if __name__ == "__main__":
    train_model()
