
import pandas as pd
import numpy as np
from datetime import date
from typing import List, Dict, Optional

class DriftDetector:
    """
    モデル性能のドリフト（劣化）を検出するクラス
    """
    def __init__(self, alert_threshold: float = 0.15, window_size: int = 30):
        self.alert_threshold = alert_threshold
        self.window_size = window_size
        self.baseline_accuracy: Optional[float] = None
        self.history: List[Dict] = []
        
    def set_baseline(self, accuracy: float):
        """ベースライン精度を設定 (例: 0.35)"""
        self.baseline_accuracy = accuracy
        print(f"Drift baseline set to: {accuracy:.2%}")
        
    def add_daily_result(self, race_date: date, accuracy: float, race_count: int):
        """日次成績を追加"""
        self.history.append({
            'date': race_date,
            'accuracy': accuracy,
            'count': race_count
        })
        
        # Keep window size
        if len(self.history) > self.window_size * 2: # Keep some buffer
            self.history = self.history[-self.window_size * 2:]
            
    def check_drift(self) -> bool:
        """
        ドリフト検知
        直近 window_size の平均精度がベースラインより一定以上下がっていたらTrue
        """
        if self.baseline_accuracy is None:
            return False
            
        if len(self.history) < 5: # Need minimal samples
            return False
            
        # Get recent window
        recent = self.history[-self.window_size:]
        df = pd.DataFrame(recent)
        
        # Weighted average by race count? Or simple average?
        # Simple average of daily accuracy might be noisy if race counts vary.
        # Let's use weighted average.
        total_races = df['count'].sum()
        if total_races == 0:
            return False
            
        weighted_acc = (df['accuracy'] * df['count']).sum() / total_races
        
        drop = self.baseline_accuracy - weighted_acc
        
        if drop > self.alert_threshold:
            print(f"DRIFT DETECTED! Baseline: {self.baseline_accuracy:.2%}, Recent: {weighted_acc:.2%}, Drop: {drop:.2%}")
            return True
            
        return False

    def analyze_drift_factors(self, recent_data: pd.DataFrame, training_data_stats: Dict):
        """
        ドリフト要因の簡易分析 (Feature drift check)
        """
        # TODO: Implement feature distribution check (PSI, KL divergence)
        pass
