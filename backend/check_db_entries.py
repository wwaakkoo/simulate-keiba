from app.predictor.sync_database import SessionLocal
from app.models.race import Race
from app.models.race_entry import RaceEntry
from sqlalchemy import func

def check_entries():
    db = SessionLocal()
    
    # Total races
    total_races = db.query(Race).count()
    print(f"Total Races: {total_races}")
    
    # Total entries
    total_entries = db.query(RaceEntry).count()
    print(f"Total Entries: {total_entries}")
    
    if total_races > 0:
        print(f"Avg Entries per Race: {total_entries / total_races:.2f}")
    
    # Check distribution
    # Group by race_id
    stats = db.query(Race.race_id, func.count(RaceEntry.id)).join(RaceEntry).group_by(Race.race_id).limit(10).all()
    print("\nSample Race Entry Counts:")
    for rid, count in stats:
        print(f"Race ID {rid}: {count} entries")
        
    db.close()

if __name__ == "__main__":
    check_entries()
