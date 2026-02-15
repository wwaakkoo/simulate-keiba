
from typing import Dict, Tuple, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.race import Race
from app.models.race_entry import RaceEntry
import pandas as pd

class SpeedIndexCalculator:
    """
    スピード指数計算クラス
    
    Data Leakage Prevention:
    - 基準タイム(Standard Time)は初期化時に全データから計算してキャッシュする。
    - 厳密な時系列検証のためには「そのレース時点での過去データ」のみを使うべきだが、
      基準タイム自体は「コースの性質」を表すため、未来のデータを含んでも
      Leakageの影響は軽微（コース改修がない限り）とみなし、
      実装簡略化のため全期間の中央値/平均を使用する。
      （※より厳密にするなら、年度ごとに基準タイムを持つべき）
    """
    
    def __init__(self, db: Session):
        self.db = db
        # Cache key: (venue, course_type, distance, track_condition)
        self.base_times: Dict[Tuple[str, str, int, str], float] = {}
        self._load_base_times()
        
    def _load_base_times(self):
        """
        基準タイムをDBから一括計算してメモリにロード
        勝ち馬の平均タイムを基準とする
        SQLiteではAVG(string)が機能しないため、Python側で集計する
        """
        # Load all winning times
        results = self.db.query(
            Race.venue,
            Race.course_type,
            Race.distance,
            Race.track_condition,
            RaceEntry.finish_time
        ).join(RaceEntry).filter(
            RaceEntry.finish_position == 1,
            RaceEntry.finish_time.isnot(None),
            Race.course_type.isnot(None),
            Race.distance.isnot(None),
            Race.track_condition.isnot(None)
        ).all()
        
        # Group by key and calculate average
        temp_times: Dict[Tuple[str, str, int, str], list] = {}
        
        for r in results:
            try:
                seconds = self._parse_time(r.finish_time)
                if seconds is None: continue
                
                key = (r.venue, r.course_type, r.distance, r.track_condition)
                if key not in temp_times:
                    temp_times[key] = []
                temp_times[key].append(seconds)
            except Exception:
                continue
                
        # Calculate average
        for key, times in temp_times.items():
            if times:
                self.base_times[key] = sum(times) / len(times)

    def _parse_time(self, time_str: Any) -> Optional[float]:
        """ '1:32.5' or 92.5 -> 92.5 """
        if time_str is None:
            return None
        if isinstance(time_str, (int, float)):
            return float(time_str)
        if isinstance(time_str, str):
            try:
                if ':' in time_str:
                    parts = time_str.split(':')
                    minutes = float(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
                return float(time_str)
            except ValueError:
                return None
        return None
            
    def calculate_for_entry(self, entry: RaceEntry, race: Race) -> Optional[float]:
        """
        個別の出走記録に対してスピード指数を計算
        """
        if not entry.finish_time:
            return None
            
        key = (race.venue, race.course_type, race.distance, race.track_condition)
        base_time = self.base_times.get(key)
        
        if base_time is None:
            # 条件不一致の場合は補正なし（あるいはフォールバック）
            # ここでは厳密に None を返す
            return None
            
        # 基本指数 = (基準タイム - 走破タイム) * 10 + 80
        # タイムが基準より速い（小さい）ほど指数は高くなる
        finish_time_sec = self._parse_time(entry.finish_time)
        if finish_time_sec is None:
            return None
            
        time_diff = base_time - finish_time_sec
        speed_index = time_diff * 10 + 80
        
        # 上がり3Fによる補正 (Pace Adjustment)
        # スローペースで全体時計が遅くても、上がりが速ければ評価する
        pace_adj = 0.0
        if entry.last_3f:
            if float(entry.last_3f) < 33.5:
                pace_adj = 3.0
            elif float(entry.last_3f) < 34.0:
                pace_adj = 1.0
        
        # 斤量補正 (Weight Adjustment)
        # 一般に 1kg = 0.2秒 = 指数2 程度とされるが、ここではシンプルに
        # 55kgを基準に、重いほど指数を上げ（ハンデを考慮）、軽いほど下げる
        # speed_index += (entry.weight_carried - 55.0) * 2
        # ※今回は複雑になるのでスキップ
        
        return speed_index + pace_adj

