"""
スクレイパー実動作検証スクリプト

実際にnetkeiba.comにアクセスし、指定したレースIDのデータを取得・保存する。
"""
import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import async_session
from app.core.init_db import init_db
from app.models import Race, RaceEntry
from app.scraper.service import ScraperService
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_scraper():
    # DB初期化
    await init_db()
    
    # 2024年 有馬記念 (中山 2500m)
    # 開催: 5回中山8日目 11R
    # ID: 202406050811
    target_race_id = "202406050811"
    
    async with async_session() as session:
        service = ScraperService(session)
        print(f"Fetching race data for ID: {target_race_id}...")
        
        try:
            # デバッグ用にHTMLを取得して保存
            html = await service._client.fetch_race_result(target_race_id)
            with open("debug_race.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Saved HTML to debug_race.html")

            # スクレイピング実行（内部で再度フェッチされるがキャッシュはないので2回叩くことになるが許容）
            # 修正: service.scrape_race は内部で fetch するので、ここでは parse_race_result_page を直接呼んでデバッグするか、
            # service のメソッドを呼ぶか。
            # service.scrape_race を呼ぶとDB保存まで行われるので、それを維持。
            race = await service.scrape_race(target_race_id)
            
            if race:
                print(f"Successfully scraped race: {race.name}")
                
                # 詳細データを再取得して表示
                stmt = (
                    select(Race)
                    .where(Race.id == race.id)
                    .options(selectinload(Race.entries))
                )
                result = await session.execute(stmt)
                loaded_race = result.scalar_one()
                
                print(f"Race Name: {loaded_race.name}")
                print(f"Date: {loaded_race.date}")
                print(f"Venue: {loaded_race.venue}")
                print(f"Course: {loaded_race.course_type} {loaded_race.distance}m")
                print(f"Entries: {len(loaded_race.entries)}")
                
                # 上位3頭を表示
                top3 = sorted(loaded_race.entries, key=lambda x: x.finish_position if x.finish_position else 999)[:3]
                for entry in top3:
                    print(f"{entry.finish_position}着: {entry.horse_number}番 (人気{entry.popularity}) Time: {entry.finish_time}")
            else:
                print("Race already exists or failed to scrape.")
                
        except Exception as e:
            logger.exception("Scraping failed")
            print(f"Error: {e}")
        finally:
            await service.close()

if __name__ == "__main__":
    asyncio.run(verify_scraper())
