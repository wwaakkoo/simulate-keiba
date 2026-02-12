from enum import Enum
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class RunningStyle(Enum):
    NIGE = "NIGE"        # 逃げ
    SENKO = "SENKO"      # 先行
    SASHI = "SASHI"      # 差し
    OIKOMI = "OIKOMI"    # 追込
    UNKNOWN = "UNKNOWN"

def determine_running_style(entries: List) -> RunningStyle:
    """
    出走記録の通過順から脚質を判定する。
    """
    if not entries:
        return RunningStyle.UNKNOWN

    position_rates = []
    
    for entry in entries:
        if not entry.passing_order:
            continue
            
        # "1-2-2-3" などの形式をパース
        try:
            positions = [int(p) for p in entry.passing_order.split("-") if p.strip()]
            if not positions:
                continue
            
            # 各地点での相対位置 (1位=0.0, 最後尾=1.0 に近い値)
            # レースごとの頭数が不明なため、1位かどうかと推移で見る
            # 簡易的に平均順位で見る
            avg_pos = sum(positions) / len(positions)
            position_rates.append(avg_pos)
        except (ValueError, AttributeError):
            continue

    if not position_rates:
        return RunningStyle.UNKNOWN

    # 全レースの平均順位
    mean_avg_pos = sum(position_rates) / len(position_rates)

    # 判定しきい値 (暫定)
    # 1〜3番手なら逃げ/先行、それ以降なら差し/追込
    if mean_avg_pos <= 2.0:
        return RunningStyle.NIGE
    elif mean_avg_pos <= 5.0:
        return RunningStyle.SENKO
    elif mean_avg_pos <= 10.0:
        return RunningStyle.SASHI
    else:
        return RunningStyle.OIKOMI
