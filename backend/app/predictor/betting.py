from typing import Dict, Optional, List, Any
from decimal import Decimal, ROUND_DOWN
import math

class KellyBettingStrategy:
    """
    Safe Kelly Criterion Betting Strategy
    資金管理を行い、ROIを最大化しつつ破産リスクを最小化する
    """
    
    def __init__(self, bankroll: int = 100000):
        """
        :param bankroll: 現在の所持金
        """
        self.bankroll = bankroll
        self.initial_bankroll = bankroll # 初期資金（ドローダウン計算用）
        
        # 安全パラメータ
        self.kelly_fraction = 0.25  # Quarter Kelly (1/4 Kelly)
        self.max_bet_pct = 0.05     # 資金の5%まで
        self.min_edge = 0.20        # 期待値20%以上のみ (EV > 1.2)
        self.min_prob = 0.10        # 勝率10%未満は賭けない (穴馬バイアス回避)
        self.max_prob = 0.80        # 勝率80%超も疑わしい
        self.min_bet_amount = 100   # 最低ベット額

    def calculate_bet(self, win_prob: float, odds: float) -> int:
        """
        最適賭け金を計算 (円単位、100円切り捨て)
        """
        # 入力検証
        if not (self.min_prob <= win_prob <= self.max_prob):
            return 0  # 確率が極端すぎる（または低すぎる）
        
        if odds <= 1.0:
            return 0  # オッズ異常
            
        # Kelly公式: f* = (bp - q) / b
        b = odds - 1.0  # 純利益倍率
        p = win_prob
        q = 1.0 - p
        
        f_star = (b * p - q) / b
        
        # 期待値チェック (Edge Check)
        expected_value = p * odds
        edge = expected_value - 1.0
        
        if edge < self.min_edge:
            return 0  # エッジ不足 (EV < 1.2)
            
        if f_star <= 0:
            return 0
            
        # Apply fractional kelly
        f_safe = f_star * self.kelly_fraction
        
        # 上限適用 (資金の5%まで)
        f_safe = min(f_safe, self.max_bet_pct)
        
        # Calculate amount
        amount = self.bankroll * f_safe
        
        # 100円単位に切り捨て
        amount_int = int(amount // 100) * 100
        
        return max(0, amount_int)
    
    def check_bet_validity(self, amount: int) -> bool:
        """
        ベット実行前の最終チェック (ドローダウンなど)
        """
        if amount < self.min_bet_amount:
            return False
            
        # チェック1: ドローダウン制限
        # current_drawdown = 1 - (self.bankroll / self.initial_bankroll)
        # if current_drawdown > 0.30:  # 30%以上の損失
        #     print("⚠️ ドローダウン30%超: ベット停止")
        #     return False
        
        # チェック2: 最低資金確保
        if self.bankroll < self.initial_bankroll * 0.5:
            # print("⚠️ 資金が初期の50%未満: ベット停止")
            return False
            
        return True
    
    def evaluate(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        予測リストに対して賭け金を計算して付与する
        predictions: [{'horse_number': 1, 'win_prob': 0.3, 'odds': 4.5}, ...]
        """
        results = []
        
        # レース全体の健全性チェック（簡易）
        # ※ 詳細なチェックはRaceAnomalyDetectorで行うが、ここでも最低限のチェック
        
        for pred in predictions:
            odds = pred.get('odds', 0.0)
            prob = pred.get('win_prob', 0.0)
            
            # 期待値計算
            ev = prob * odds
            
            # Calculate Bet
            bet_amount = self.calculate_bet(prob, odds)
            
            # Validity Check
            if bet_amount > 0:
                if not self.check_bet_validity(bet_amount):
                    bet_amount = 0
            
            results.append({
                **pred,
                'expected_value': ev,
                'bet_amount': bet_amount,
                'recommendation': 'BUY' if bet_amount > 0 else 'SKIP'
            })
            
        return results

class VarianceReductionStrategy:
    """
    分散を抑えるための複数のベッティング戦略を提供するクラス
    """
    def __init__(self, strategy_type: str = 'low_variance'):
        self.strategy_type = strategy_type
        
    def evaluate(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if self.strategy_type == 'low_variance':
            return self._low_variance_strategy(predictions)
        elif self.strategy_type == 'high_volume':
            return self._high_volume_strategy(predictions)
        elif self.strategy_type == 'diversified':
            return self._diversified_strategy(predictions)
        else:
            return []

    def _low_variance_strategy(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        戦略1: 低オッズ（本命寄り）に集中
        オッズ3.0倍以下、EV > 1.3
        """
        results = []
        candidates = [p for p in predictions if p.get('odds', 999) <= 3.0]
        
        if not candidates:
            return self._return_empty_results(predictions)
            
        best_bet = None
        max_ev = -1
        
        for p in candidates:
            prob = p.get('win_prob', 0.0)
            odds = p.get('odds', 0.0)
            ev = prob * odds
            
            if ev > 1.3:
                if ev > max_ev:
                    max_ev = ev
                    best_bet = p
        
        # 結果構築 (他はSKIP)
        for p in predictions:
            is_target = (best_bet and p['horse_number'] == best_bet['horse_number'])
            results.append({
                **p,
                'expected_value': p.get('win_prob', 0) * p.get('odds', 0),
                'bet_amount': 1000 if is_target else 0, # 固定額 or 資金管理? 今は簡易的に固定
                'recommendation': 'BUY' if is_target else 'SKIP',
                'strategy': 'low_variance'
            })
            
        return results

    def _high_volume_strategy(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        戦略2: ベット数を増やす（基準を緩和）
        EV > 1.15 の上位3頭
        """
        results = []
        # EV計算
        for p in predictions:
            p['temp_ev'] = p.get('win_prob', 0) * p.get('odds', 0)
            
        # EV > 1.15 フィルタ
        candidates = [p for p in predictions if p['temp_ev'] > 1.15]
        
        # 上位3頭
        candidates.sort(key=lambda x: x['temp_ev'], reverse=True)
        top3_ids = {p['horse_number'] for p in candidates[:3]}
        
        for p in predictions:
            is_target = p['horse_number'] in top3_ids
            results.append({
                **p,
                'expected_value': p['temp_ev'],
                'bet_amount': 500 if is_target else 0,
                'recommendation': 'BUY' if is_target else 'SKIP',
                'strategy': 'high_volume'
            })
            
        return results

    def _diversified_strategy(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        戦略3: 分散投資 (単勝 + 複勝想定)
        ※ 現在のシステムは単勝メインだが、シミュレーション用に推奨情報を付与
        """
        # 単勝本命
        results = []
        sorted_preds = sorted(predictions, key=lambda x: x.get('win_prob', 0) * x.get('odds', 0), reverse=True)
        if not sorted_preds:
            return self._return_empty_results(predictions)
            
        main_bet = sorted_preds[0]
        main_ev = main_bet.get('win_prob', 0) * main_bet.get('odds', 0)
        
        for p in predictions:
            res = {
                **p,
                'expected_value': p.get('win_prob', 0) * p.get('odds', 0),
                'bet_amount': 0,
                'bet_type': [],
                'recommendation': 'SKIP'
            }
            
            # 単勝
            if p == main_bet and main_ev > 1.25:
                res['bet_amount'] += 1000
                res['bet_type'].append('WIN')
                res['recommendation'] = 'BUY'
                
            # 複勝 (簡易ロジック: 上位人気でオッズがついている場合)
            # ※ 複勝オッズや確率はここにはないかもしれないが、簡易的に
            if p.get('win_prob', 0) > 0.2 and p.get('odds', 0) > 5.0: # 穴っぽい
                 # 複勝適正ありとみなす
                 pass
            
            results.append(res)
            
        return results

    def _return_empty_results(self, predictions):
        return [{**p, 'bet_amount': 0, 'recommendation': 'SKIP'} for p in predictions]

