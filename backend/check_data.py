from app.predictor.sync_database import SessionLocal
from app.models.race import Race

def check_data_quality():
    db = SessionLocal()
    races = db.query(Race).all()
    print(f"Total races: {len(races)}")
    
    if not races:
        print("No races found.")
        return

    entry_counts = [len(r.entries) for r in races]
    avg_entries = sum(entry_counts) / len(races)
    print(f"Average entries per race: {avg_entries:.2f}")
    print(f"Min entries: {min(entry_counts)}")
    print(f"Max entries: {max(entry_counts)}")
    
    # Distribution
    import collections
    counter = collections.Counter(entry_counts)
    print("Entry count distribution:")
    for k in sorted(counter.keys()):
        print(f"{k}: {counter[k]}")

    db.close()

if __name__ == "__main__":
    check_data_quality()
