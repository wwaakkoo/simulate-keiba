"""
レースメタデータの修復用スクリプト
"Unknown Race" やダミー日付になっているレース情報を再スクレイピングして更新する。
"""
import asyncio
import logging
import random
import sys
from datetime import datetime, date

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# パス解決
import os
sys.path.append(os.getcwd())

from app.core.database import get_db, async_session as SessionLocal
from app.models.race import Race
from app.scraper.client import ScraperClient
from app.scraper.parser import parse_race_result_page


# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("repair_metadata.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


async def repair_metadata():
    client = ScraperClient()
    
    async with SessionLocal() as db:
        # 修復対象のレースを取得 (名前が "Unknown Race" または 日付が今日になってしまっているもの)
        # ただし日付判定はSQLでは難しいので、まずは名前で判定
        stmt = select(Race).where(Race.name == "Unknown Race")
        result = await db.execute(stmt)
        races = result.scalars().all()
        
        logger.info(f"Metadata Repair Target: {len(races)} races")
        
        processed = 0
        
        try:
            for race in races:
                try:
                    logger.info(f"Repairing metadata for {race.race_id}...")
                    
                    # HTML取得
                    html = await client.fetch_race_result(race.race_id)
                    
                    # パース
                    parsed = parse_race_result_page(html, race.race_id)
                    info = parsed.race_info
                    
                    # データの更新
                    # 日付文字列をdateオブジェクトに変換
                    # parser returns "YYYY-MM-DD" or None
                    race_date_obj: date | None = None
                    if info.date:
                        try:
                            race_date_obj = datetime.strptime(info.date, "%Y-%m-%d").date()
                        except ValueError:
                            pass
                            
                    # Update statement
                    update_values = {
                        "name": info.name,
                        "venue": info.venue,
                        "course_type": info.course_type,
                        "distance": info.distance,
                        "direction": info.direction,
                        "weather": info.weather,
                        "track_condition": info.track_condition,
                        "race_class": info.race_class,
                        "num_entries": info.num_entries
                    }
                    if race_date_obj:
                        update_values["date"] = race_date_obj
                        
                    await db.execute(
                        update(Race)
                        .where(Race.id == race.id)
                        .values(**update_values)
                    )
                    await db.commit()
                    
                    processed += 1
                    logger.info(f"Updated {race.race_id}: {info.name}")
                    
                    # Wait slightly
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error repairing {race.race_id}: {e}")
                    await db.rollback()
                    
        finally:
            await client.close()
            
    logger.info(f"Repair complete. Updated {processed} races.")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(repair_metadata())
