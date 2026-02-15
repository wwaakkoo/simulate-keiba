from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.race import Race
from app.models.race_entry import RaceEntry
from app.models.horse import Horse
from app.predictor.logic import determine_running_style, RunningStyle

class FeatureFactory:
    """特徴量生成クラス"""
    
    def __init__(self, db: Session):
        self.db = db
    
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
        
        for entry in entries:
            features = self._generate_horse_features(entry, race)
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
    
    def _generate_horse_features(self, entry: RaceEntry, race: Race) -> List[float]:
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
        if hasattr(race, 'distance') and race.distance:
            distance_entries = [e for e in past_entries
                                if e.race.distance and abs(e.race.distance - race.distance) <= 200 
                                and e.finish_position is not None]
            avg_position_at_distance = (sum([e.finish_position for e in distance_entries]) / len(distance_entries)
                                        if distance_entries else avg_position_all)
        else:
            avg_position_at_distance = avg_position_all
        
        # 4. 脚質のエンコード
        running_style = determine_running_style(past_entries)
        
        running_style_map = {
            RunningStyle.NIGE: 1.0,
            RunningStyle.SENKO: 2.0,
            RunningStyle.SASHI: 3.0,
            RunningStyle.OIKOMI: 4.0,
            RunningStyle.UNKNOWN: 2.5
        }
        running_style_encoded = running_style_map.get(running_style, 2.5)
        
        # 5. レース条件
        race_distance = float(race.distance) if race.distance else 1600.0
        race_surface_encoded = 1.0 if race.course_type == '芝' else 0.0
        num_horses = float(len(race.entries)) if race.entries else 10.0
        
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
            avg_position_trend
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
            'avg_position_trend'
        ]
