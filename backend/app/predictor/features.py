from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.race import Race
from app.models.race_entry import RaceEntry
from app.models.horse import Horse
from app.predictor.logic import determine_running_style, RunningStyle
import numpy as np
import re

class FeatureFactory:
    """特徴量生成クラス"""
    
    def __init__(self, db: Session):
        self.db = db
        self.jockey_stats_cache = {} # Cache for jockey stats within a session
    
    def generate_features_for_race(self, race_id: int) -> Dict[str, Any]:
        """レース全体の特徴量を生成"""
        race = self.db.query(Race).filter(Race.id == race_id).first()
        if not race:
            raise ValueError(f"Race not found: {race_id}")
            
        entries = race.entries
        
        features_list = []
        horse_names = []
        horse_numbers = []
        horse_ids = []
        
        # Calculate race-level stats
        all_odds = [float(e.odds) if e.odds is not None else 99.9 for e in entries]
        odds_ranks = np.argsort(np.argsort(all_odds)) + 1
        
        all_weights = [float(e.horse_weight) for e in entries if e.horse_weight]
        avg_weight = sum(all_weights) / len(all_weights) if all_weights else 480.0
        
        for i, entry in enumerate(entries):
            # Calculate weight diff vs avg
            weight_diff_vs_avg = (float(entry.horse_weight) - avg_weight) if entry.horse_weight else 0.0
            
            features = self._generate_horse_features(
                entry, race, 
                odds_rank=float(odds_ranks[i]),
                weight_diff_vs_avg=weight_diff_vs_avg
            )
            features_list.append(features)
            
            # Get horse name properly
            horse_name = entry.horse.name if entry.horse else "Unknown"
            if horse_name == "Unknown" and entry.horse_id:
                horse = self.db.query(Horse).get(entry.horse_id)
                if horse:
                    horse_name = horse.name
            
            horse_names.append(horse_name)
            horse_numbers.append(entry.horse_number)
            horse_ids.append(entry.horse.horse_id)
        
        return {
            'features': features_list,
            'horse_names': horse_names,
            'horse_numbers': horse_numbers,
            'horse_ids': horse_ids
        }
    
    def _generate_horse_features(self, entry: RaceEntry, race: Race, odds_rank: float = 0.0, weight_diff_vs_avg: float = 0.0) -> List[float]:
        """1頭分の特徴量を生成"""
        
        # 過去の全出走を取得（自分自身を除く）
        past_entries = self.db.query(RaceEntry).join(Race).filter(
            RaceEntry.horse_id == entry.horse_id,
            RaceEntry.id != entry.id,
            Race.date < race.date
        ).order_by(Race.date.desc()).all()
        
        # 1. 過去実績の計算
        if not past_entries:
            avg_position_all = 9.0
            avg_position_recent3 = 9.0
            win_rate = 0.0
            place_rate = 0.0
            avg_position_trend = 0.0 # New
        else:
            positions = [e.finish_position for e in past_entries if e.finish_position is not None]
            if not positions:
                avg_position_all = 9.0
                win_rate = 0.0
                place_rate = 0.0
            else:
                avg_position_all = sum(positions) / len(positions)
                win_rate = len([p for p in positions if p == 1]) / len(positions)
                place_rate = len([p for p in positions if p <= 3]) / len(positions)
            
            recent_entries = [e for e in past_entries if e.finish_position is not None][:3]
            if recent_entries:
                recent_positions = [e.finish_position for e in recent_entries]
                avg_position_recent3 = sum(recent_positions) / len(recent_positions)
            else:
                avg_position_recent3 = 9.0
            
            # Trend (Slope of last 5 races) - Simplified: (Avg of first 2 - Avg of last 2)
            # Actually simplest is: Recent Avg - Overall Avg (Positive means worsening, Negative means improving)
            # Or linear regression slope.
            # Let's use simple difference: (Last 3 Avg) - (Overall Avg)
            avg_position_trend = avg_position_recent3 - avg_position_all

        # 2. コース適性 (芝/ダート)
        if hasattr(race, 'course_type') and race.course_type:
            # Note: Assuming course_type is exactly '芝' or 'ダート'.
            pass
        
        # Turf
        turf_entries = [e for e in past_entries if e.race.course_type == '芝' and e.finish_position is not None]
        avg_position_on_turf = sum([e.finish_position for e in turf_entries]) / len(turf_entries) if turf_entries else avg_position_all
        
        # Dirt
        dirt_entries = [e for e in past_entries if e.race.course_type == 'ダート' and e.finish_position is not None]
        avg_position_on_dirt = sum([e.finish_position for e in dirt_entries]) / len(dirt_entries) if dirt_entries else avg_position_all

        # 3. 距離適性（±200m以内を同距離帯とする）
        # This is now just a general distance aptitude, not specific to the current race distance.
        # The new distance_aptitude feature will cover the current race distance.
        if hasattr(race, 'distance') and race.distance:
            distance_entries = [e for e in past_entries
                                if e.race.distance and abs(e.race.distance - race.distance) <= 200 
                                and e.finish_position is not None]
            avg_position_at_distance = (sum([e.finish_position for e in distance_entries]) / len(distance_entries)
                                        if distance_entries else avg_position_all)
        else:
            avg_position_at_distance = avg_position_all
        
        # Calculate race conditions early as they are used by other features
        race_distance = float(race.distance) if race.distance else 1600.0
        race_surface_encoded = 1.0 if race.course_type == '芝' else 0.0
        num_horses = float(len(race.entries)) if race.entries else 10.0

        # 4. Distance Aptitude (New Phase E-2)
        # Difference between current distance and average distance of past top-3 finishes
        distance_aptitude = 0.0
        good_past_entries = [e for e in past_entries if e.finish_position is not None and e.finish_position <= 3]
        if good_past_entries:
            past_distances = [e.race.distance for e in good_past_entries if e.race and e.race.distance]
            if past_distances:
                avg_good_dist = sum(past_distances) / len(past_distances)
                distance_aptitude = abs(race_distance - avg_good_dist)
        
        # 5. 脚質のエンコード
        running_style = determine_running_style(past_entries)
        
        running_style_map = {
            RunningStyle.NIGE: 1.0,
            RunningStyle.SENKO: 2.0,
            RunningStyle.SASHI: 3.0,
            RunningStyle.OIKOMI: 4.0,
            RunningStyle.UNKNOWN: 0.0
        }
        running_style_encoded = running_style_map.get(running_style, 0.0)
        
        # 6. オッズ
        odds = float(entry.odds) if entry.odds is not None else 50.0

        # === Medium Features ===

        # 7. Days Since Last Race
        if past_entries:
            last_race = past_entries[0].race
            delta = (race.date - last_race.date).days
            rotation_days = float(delta)
        else:
            rotation_days = 90.0 # Default for first timers or unknown

        # 8. Track Condition Aptitude (馬場適性)
        # Assuming race.track_condition is like "良", "重"
        current_condition = race.track_condition or "良"
        condition_entries = [e for e in past_entries if e.race.track_condition == current_condition and e.finish_position is not None]
        if condition_entries:
             avg_position_condition = sum([e.finish_position for e in condition_entries]) / len(condition_entries)
        else:
             avg_position_condition = avg_position_all # Fallback

        # 9. Weight Change
        weight_change = float(entry.horse_weight_diff) if entry.horse_weight_diff is not None else 0.0

        # 10. Jockey Match (Win/Place rate with this jockey)
        current_jockey = entry.jockey
        if current_jockey:
            jockey_entries = [e for e in past_entries if e.jockey == current_jockey and e.finish_position is not None]
            if jockey_entries:
                jockey_match_win_rate = len([e for e in jockey_entries if e.finish_position == 1]) / len(jockey_entries)
            else:
                jockey_match_win_rate = 0.0 # No history with this jockey
        else:
             jockey_match_win_rate = 0.0

        # 11. Jockey General Stats (Overall skill)
        cache_key = (current_jockey, race.date.isoformat())
        if current_jockey and cache_key in self.jockey_stats_cache:
            jockey_win_rate_all, jockey_place_rate_all = self.jockey_stats_cache[cache_key]
        elif current_jockey:
            all_j_entries = self.db.query(RaceEntry).join(Race).filter(
                RaceEntry.jockey == current_jockey,
                Race.date < race.date
            ).all()
            if all_j_entries:
                j_positions = [e.finish_position for e in all_j_entries if e.finish_position is not None]
                if j_positions:
                    jockey_win_rate_all = len([p for p in j_positions if p == 1]) / len(j_positions)
                    jockey_place_rate_all = len([p for p in j_positions if p <= 3]) / len(j_positions)
                else:
                    jockey_win_rate_all = 0.0
                    jockey_place_rate_all = 0.0
            else:
                jockey_win_rate_all = 0.0
                jockey_place_rate_all = 0.0
            
            self.jockey_stats_cache[cache_key] = (jockey_win_rate_all, jockey_place_rate_all)
        else:
            jockey_win_rate_all = 0.0
            jockey_place_rate_all = 0.0

        # 12. Horse Age & Sex
        age = 3.0
        sex_encoded = 0.0 # 0=牡/セ, 1=牝
        if entry.horse:
            if entry.horse.sex and "牝" in entry.horse.sex:
                sex_encoded = 1.0
            
            if entry.horse.birthday and race.date:
                # e.g. "2020年3月15日"
                try:
                    birth_year_match = re.search(r'(\d+)年', entry.horse.birthday)
                    if birth_year_match:
                        birth_year = int(birth_year_match.group(1))
                        age = float(race.date.year - birth_year)
                except:
                    pass

        return [
            avg_position_all,
            avg_position_recent3,
            win_rate,
            place_rate,
            avg_position_on_turf,
            avg_position_on_dirt,
            avg_position_at_distance,
            running_style_encoded,
            race_distance,
            race_surface_encoded,
            num_horses,
            odds,
            # Medium
            rotation_days,
            avg_position_condition,
            weight_change,
            jockey_match_win_rate,
            avg_position_trend,
            # New Phase E-2
            odds_rank,
            jockey_win_rate_all,
            jockey_place_rate_all,
            age,
            sex_encoded,
            weight_diff_vs_avg,
            distance_aptitude
        ]
    
    @staticmethod
    def get_feature_names() -> List[str]:
        """特徴量の名前リスト（順序重要）"""
        return [
            'avg_position_all',
            'avg_position_recent3',
            'win_rate',
            'place_rate',
            'avg_position_on_turf',
            'avg_position_on_dirt',
            'avg_position_at_distance',
            'running_style_encoded',
            'race_distance',
            'race_surface_encoded',
            'num_horses',
            'odds',
            'rotation_days',
            'avg_position_condition',
            'weight_change',
            'jockey_match_win_rate',
            'avg_position_trend',
            'odds_rank',
            'jockey_win_rate_all',
            'jockey_place_rate_all',
            'age',
            'sex_encoded',
            'weight_diff_vs_avg',
            'distance_aptitude'
        ]
