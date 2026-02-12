import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.models import Race, Horse, RaceEntry
from datetime import date
from app.core.database import get_db

# テスト用DBセッションフィクスチャ
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models import Base

@pytest.fixture
async def test_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = session_factory()
    
    async def override_get_db() -> AsyncSession:
        yield session
    
    app.dependency_overrides[get_db] = override_get_db
    yield session
    
    await session.close()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_analyze_horse_stats(test_session: AsyncSession) -> None:
    # データ投入
    race = Race(
        race_id="202401010101", name="テストレース", date=date(2024, 1, 1),
        venue="東京", course_type="芝", distance=2000, num_entries=16
    )
    horse = Horse(horse_id="2021101234", name="テスト逃げ馬", sex="牡")
    test_session.add_all([race, horse])
    await test_session.flush()
    
    # 逃げた履歴 (通過順 1-1-1)
    entry = RaceEntry(
        race_id=race.id, horse_id=horse.id, 
        passing_order="1-1-1", finish_position=1, last_3f=34.0
    )
    test_session.add(entry)
    await test_session.commit()

    # APIコール
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/analysis/horses/{horse.horse_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "テスト逃げ馬"
    assert data["style"] == "NIGE"
    assert data["stats"]["speed"] == 90.0  # (100 - (34.0 - 33.0)*10) = 90
    assert data["stats"]["races_count"] == 1.0
