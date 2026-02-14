
import asyncio
import logging
import sys
from app.scraper.client import ScraperClient
import app.scraper.parser
print(f"DEBUG: parser file: {app.scraper.parser.__file__}")
from app.scraper.parser import parse_race_result_page

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_race(race_id: str):
    print(f"--- Debugging Race ID: {race_id} ---")
    client = ScraperClient()
    try:
        html = await client.fetch_race_result(race_id)
        if not html:
            print("Failed to fetch HTML")
            return

        print(f"HTML fetched. Length: {len(html)}")
        
        # Save HTML for inspection
        with open(f"debug_{race_id}.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved HTML to debug_{race_id}.html")

        # Parse
        print("Parsing...")
        parsed = parse_race_result_page(html, race_id)
        
        print("\n--- Parsed Result ---")
        print(f"Race Name: {parsed.race_info.name}")
        print(f"Entries Found: {len(parsed.entries)}")
        
        for i, entry in enumerate(parsed.entries):
            print(f"Entry {i+1}: {entry.horse_number} {entry.horse_name} (Rank: {entry.finish_position})")
            
        if len(parsed.entries) <= 1:
            print("\n!!! WARNING: Only 0 or 1 entry found. This is likely the bug. !!!")
            
            # Additional debug info about the table
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            table = soup.select_one("table.race_table_01, table.RaceTable01")
            if table:
                rows = table.select("tr")
                print(f"Table found. Total rows (including header): {len(rows)}")
                if len(rows) > 1:
                    print("Row 1 (Header?):", rows[0].get_text(strip=True)[:50] + "...")
                    print("Row 2 (First Data?):", rows[1].get_text(strip=True)[:50] + "...")
            else:
                print("Table NOT found with selector 'table.race_table_01, table.RaceTable01'")

    finally:
        await client.close()

if __name__ == "__main__":
    target_race_id = "202406050811" 
    if len(sys.argv) > 1:
        target_race_id = sys.argv[1]
        
    # Run the fetch/parse
    asyncio.run(debug_race(target_race_id))

    # Detailed HTML Inspection
    print("\n--- Detailed HTML Inspection ---")
    try:
        with open(f"debug_{target_race_id}.html", "r", encoding="utf-8") as f:
            html = f.read()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("table.race_table_01, table.RaceTable01")
        
        with open("debug_inspection.log", "w", encoding="utf-8") as log_file:
            if table:
                rows = table.select("tr")
                log_file.write(f"Total Rows: {len(rows)}\n")
                for i, row in enumerate(rows):
                    cells = row.select("td")
                    if len(cells) > 2:
                        horse_num_text = cells[2].get_text(strip=True)
                        log_file.write(f"Row {i}: {len(cells)} cells, HorseNum: '{horse_num_text}'\n")
                    else:
                        log_file.write(f"Row {i}: {len(cells)} cells (No HorseNum cell)\n")
                        headers = row.select("th")
                        if headers:
                            header_txt = " | ".join([h.get_text(strip=True) for h in headers])
                            log_file.write(f"  Header: {header_txt}\n")
            else:
                log_file.write("Table not found in saved HTML.\n")
    except Exception as e:
        print(f"Error checking HTML: {e}")
