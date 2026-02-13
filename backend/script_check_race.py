import asyncio
from app.core.database import async_session
from app.models import Race
from sqlalchemy import select

async def main():
    async with async_session() as session:
        stmt = select(Race).where(Race.num_entries > 0).limit(1)
        result = await session.execute(stmt)
        race = result.scalar_one_or_none()
        if race:
            print(f"RACE_ID:{race.race_id}")
        else:
            print("NO_RACE_FOUND")

if __name__ == "__main__":
    asyncio.run(main())
