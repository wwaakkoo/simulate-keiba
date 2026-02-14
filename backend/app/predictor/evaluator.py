import numpy as np
from sklearn.metrics import mean_squared_error
from app.predictor.sync_database import SessionLocal
from app.predictor.features import FeatureFactory
from app.models.race import Race
import lightgbm as lgb
import os

def evaluate_model():
    """モデルの精度を評価"""
    db = SessionLocal()
    factory = FeatureFactory(db)
    
    model_path = 'models/race_predictor_v1.pkl'
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}")
        return

    # モデルをロード
    model = lgb.Booster(model_file=model_path)
    
    # テストセットを取得（最新10%）
    # Note: Trainer logic used 80/10/10 split.
    # Train: :0.8, Valid: 0.8:0.9, Test: 0.9:
    races = db.query(Race).order_by(Race.date).all()
    n = len(races)
    test_start = int(n * 0.9)
    test_races = races[test_start:]
    
    print(f"Evaluating on {len(test_races)} test races...")
    
    total_rmse = []
    top3_hit = 0
    total_predictions = 0
    
    valid_races_count = 0

    for race in test_races:
        try:
            result = factory.generate_features_for_race(race.id)
            if not result['features']:
                continue
                
            X = np.array(result['features'])
            
            # 予測
            predictions = model.predict(X)
            
            # 予測着順でソート（昇順 - 小さいほど良い）
            # predictions is array of floats (predicted positions)
            sorted_indices = np.argsort(predictions)
            
            # The indices in sorted_indices correspond to indices in result['horse_names']
            # Predicted Top 3 horses (indices)
            predicted_top3_indices = set(sorted_indices[:3])
            
            # Actual Top 3 horses
            actual_top3_indices = set()
            feature_vectors_with_actual = []
            
            # Map back to actual results
            # We need to find which index in X corresponds to which actual finish position
            current_race_y_true = []
            valid_race_preds = []

            for i, horse_name in enumerate(result['horse_names']):
                entry = next((e for e in race.entries if e.horse.name == horse_name), None)
                if not entry and race.entries:
                     # Fallback check
                     pass
                
                if entry and entry.finish_position is not None:
                    if entry.finish_position <= 3:
                        actual_top3_indices.add(i)
                    current_race_y_true.append(entry.finish_position)
                    valid_race_preds.append(predictions[i])
            
            # If we don't have finish positions for all predicted horses, RMSE calculation needs care.
            # But usually we only predict for horses in the race. 
            # If some horses DNF, they might have None position.
            # For RMSE, strictly speaking we should only compare horses that finished.
            
            if len(current_race_y_true) > 0:
                 rmse = np.sqrt(mean_squared_error(current_race_y_true, valid_race_preds))
                 total_rmse.append(rmse)
            
            # Top 3 Hit Logic
            # Intersection of predicted indices and actual indices
            hits = len(predicted_top3_indices & actual_top3_indices)
            top3_hit += hits
            
            # Total theoretical max hits is 3 per race (or less if <3 horses)
            # Accuracy = (Total Hits) / (Total Races * 3)
            # This is "Micro-average" accuracy of picking a Top 3 horse.
            
            valid_races_count += 1
            
        except Exception as e:
            print(f"Error evaluating race {race.id}: {e}")
            continue
    
    if valid_races_count == 0:
        print("No valid test races found.")
        return

    # 総合評価
    avg_rmse = np.mean(total_rmse)
    top3_accuracy = (top3_hit / (valid_races_count * 3)) * 100
    
    print("\n" + "="*50)
    print("📊 Evaluation Results")
    print("="*50)
    print(f"Test Races: {valid_races_count}")
    print(f"Average RMSE: {avg_rmse:.3f} 着")
    print(f"Top-3 Precision (3着内的中率): {top3_accuracy:.1f}%")
    print(f"  (Total Hits: {top3_hit} / Max: {valid_races_count * 3})")
    
    # Threshold Optimization Analysis
    print("\n📦 Threshold Optimization Analysis")
    optimize_threshold(model, test_races, factory)

    print("\n【Target Comparison】")
    print(f"Random Guess RMSE: ~6.0")
    print(f"Random Guess Top-3 Precision: ~20-30% (depending on field size)")
    
    if avg_rmse < 4.0:
        print("\n✅ Goal Achieved: Validation successful")
    else:
        print("\n⚠️ Needs Improvement")
    
    db.close()

def optimize_threshold(model, races, factory):
    """Top-3精度を最大化する閾値を探索"""
    print("Finding optimal classification threshold for Top-3 prediction...")
    
    all_preds = []
    all_actual_top3 = [] # 1 if in Top 3, 0 otherwise
    
    for race in races:
        try:
            result = factory.generate_features_for_race(race.id)
            if not result['features']: continue
            X = np.array(result['features'])
            preds = model.predict(X)
            
            for i, horse_name in enumerate(result['horse_names']):
                entry = next((e for e in race.entries if e.horse.name == horse_name), None)
                if entry and entry.finish_position is not None:
                    all_preds.append(preds[i])
                    all_actual_top3.append(1 if entry.finish_position <= 3 else 0)
        except Exception:
            continue
            
    if not all_preds:
        print("No data for threshold optimization.")
        return

    all_preds = np.array(all_preds)
    all_actual_top3 = np.array(all_actual_top3)
    
    best_threshold = 3.5
    best_f1 = 0.0
    best_acc = 0.0
    
    # Try thresholds from 1.0 to 10.0
    print(f"Analyzing {len(all_preds)} predictions...")
    headers = f"{'Threshold':<10} {'Precision':<10} {'Recall':<10} {'F1':<10}"
    print("-" * 40)
    print(headers)
    print("-" * 40)
    
    for th in np.arange(2.0, 6.0, 0.5):
        # Predicted Positive: Score <= th (lower score is better rank)
        pred_pos = (all_preds <= th)
        actual_pos = (all_actual_top3 == 1)
        
        # True Positive
        tp = np.sum(pred_pos & actual_pos)
        # False Positive
        fp = np.sum(pred_pos & ~actual_pos)
        # False Negative
        fn = np.sum(~pred_pos & actual_pos)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"{th:<10.1f} {precision:<10.3f} {recall:<10.3f} {f1:<10.3f}")
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = th
            
    print("-" * 40)
    print(f"Best Threshold (F1): {best_threshold:.1f} (F1: {best_f1:.3f})")
    print("Note: This threshold can be used to flag 'High Confidence' predictions in UI.")

if __name__ == "__main__":
    evaluate_model()
