import sqlite3
import os

def check_ml_readiness():
    possible_paths = [
        "data/keiba.db",
        "../data/keiba.db",
        "../../data/keiba.db"
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
            
    if db_path is None:
        print("ERROR: keiba.db not found.")
        return

    print(f"DB_PATH: {os.path.abspath(db_path)}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Race Count
        try:
            cursor.execute("SELECT COUNT(*) FROM races")
            race_count = cursor.fetchone()[0]
            print(f"RACE_COUNT: {race_count}")
        except Exception as e:
             print(f"RACE_COUNT: ERROR {e}")
        
        # 2. Horse Race Count Distribution
        try:
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT horse_id) as unique_horses,
                    AVG(race_count) as avg_races_per_horse
                FROM (
                    SELECT horse_id, COUNT(*) as race_count
                    FROM race_entries
                    GROUP BY horse_id
                )
            """)
            result = cursor.fetchone()
            if result and result[0] is not None:
                horses, avg_races = result
                print(f"UNIQUE_HORSES: {horses}")
                print(f"AVG_RACES: {avg_races:.2f}")
            else:
                print("UNIQUE_HORSES: 0")
                print("AVG_RACES: 0.00")
        except Exception as e:
             print(f"HORSE_STATS: ERROR {e}")
        
        # 3. Data Completeness
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN finish_position IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pos_rate,
                    SUM(CASE WHEN finish_time IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as time_rate,
                    SUM(CASE WHEN odds IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as odds_rate
                FROM race_entries
            """)
            result = cursor.fetchone()
            if result and result[0] > 0:
                total, pos_rate, time_rate, odds_rate = result
                print(f"DATA_COMPLETENESS_TOTAL: {total}")
                print(f"POS_RATE: {pos_rate:.1f}")
                print(f"TIME_RATE: {time_rate:.1f}")
                print(f"ODDS_RATE: {odds_rate:.1f}")
            else:
                print("DATA_COMPLETENESS_TOTAL: 0")
        except Exception as e:
             print(f"DATA_COMPLETENESS: ERROR {e}")

        conn.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_ml_readiness()
