import asyncio
import sys
import os
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session
from app.scraper.service import ScraperService

# Add backend to path
sys.path.append(os.getcwd())

async def bulk_scrape(start_year: int, end_year: int):
    """
    指定期間の土日のレースデータを一括収集する。
    (中央競馬は基本的に土日開催のため)
    """
    async with async_session() as session:
        service = ScraperService(session)
        
        current_date = date(start_year, 1, 1)
        end_date = date(end_year, 12, 31)
        
        print(f"Starting bulk scrape from {current_date} to {end_date}")
        
        total_days = (end_date - current_date).days + 1
        processed = 0
        
        while current_date <= end_date:
            # 土日(5, 6)のみをターゲットにする（効率化のため）
            # もし地方競馬も含めるならこのチェックを外す
            if current_date.weekday() >= 5:
                date_str = current_date.strftime("%Y%m%d")
                print(f"[{processed}/{total_days}] Scraping {date_str}...")
                try:
                    result = await service.scrape_date(date_str)
                    print(f"  Result: {result['new']} new, {result['skipped']} skipped, {result['errors']} errors")
                except Exception as e:
                    print(f"  Error on {date_str}: {e}")
                
                # 防御的なスリープ（netkeibaへの負荷軽減）
                await asyncio.sleep(2.0)
            
            current_date += timedelta(days=1)
            processed += 1
            
        await service.close()
        print("Bulk scrape completed.")

if __name__ == "__main__":
    # テストとして2024年1月の最初の1週間のみ実行
    asyncio.run(bulk_scrape(2024, 2024)) # Note: internal logic selects weekends

