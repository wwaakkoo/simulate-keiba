"""
APIエンドポイントのテスト
"""

from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.main import app
from app.models import Base, Horse, Race, RaceEntry


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def test_session() -> AsyncSession:  # type: ignore[misc]
    """テスト用DBセッション（APIテスト用）"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = session_factory()

    # FastAPIの依存性を上書き
    async def override_get_db() -> AsyncSession:  # type: ignore[misc]
        yield session  # type: ignore[misc]

    app.dependency_overrides[get_db] = override_get_db

    yield session  # type: ignore[misc]

    await session.close()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

    app.dependency_overrides.clear()


@pytest.fixture
async def seeded_session(test_session: AsyncSession) -> AsyncSession:
    """テストデータがシードされたセッション"""
    race = Race(
        race_id="202506010101",
        name="テスト記念",
        date=date(2025, 6, 1),
        venue="東京",
        course_type="芝",
        distance=2000,
        direction="左",
        weather="晴",
        track_condition="良",
        race_class="G1",
        num_entries=3,
    )
    horse = Horse(
        horse_id="2021104567",
        name="テストディープ",
        sex="牡",
        trainer="テスト調教師",
    )
    test_session.add_all([race, horse])
    await test_session.flush()

    entry = RaceEntry(
        race_id=race.id,
        horse_id=horse.id,
        bracket_number=3,
        horse_number=5,
        jockey="テスト騎手",
        weight_carried=57.0,
        odds=3.5,
        popularity=1,
        finish_position=1,
        finish_time="1:59.5",
        passing_order="3-3-2-1",
        last_3f=33.8,
    )
    test_session.add(entry)
    await test_session.commit()

    return test_session


@pytest.mark.asyncio
async def test_list_races_empty(test_session: AsyncSession) -> None:
    """レースが無い場合は空リストが返ること"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/races")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_races_with_data(seeded_session: AsyncSession) -> None:
    """レース一覧が正しく返ること"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/races")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["race_id"] == "202506010101"
    assert data[0]["name"] == "テスト記念"
    assert data[0]["venue"] == "東京"


@pytest.mark.asyncio
async def test_get_race_detail(seeded_session: AsyncSession) -> None:
    """レース詳細（出走馬含む）が正しく返ること"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/races/202506010101")

    assert response.status_code == 200
    data = response.json()
    assert data["race_id"] == "202506010101"
    assert data["name"] == "テスト記念"
    assert data["distance"] == 2000
    assert len(data["entries"]) == 1
    assert data["entries"][0]["horse"]["name"] == "テストディープ"
    assert data["entries"][0]["passing_order"] == "3-3-2-1"


@pytest.mark.asyncio
async def test_get_race_not_found(test_session: AsyncSession) -> None:
    """存在しないレースIDで404が返ること"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/races/999999999999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_horse(seeded_session: AsyncSession) -> None:
    """馬の詳細情報が返ること"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/horses/2021104567")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "テストディープ"
    assert data["horse_id"] == "2021104567"


@pytest.mark.asyncio
async def test_get_horse_not_found(test_session: AsyncSession) -> None:
    """存在しない馬IDで404が返ること"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/horses/nonexistent")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_races_filter_by_venue(seeded_session: AsyncSession) -> None:
    """会場名でフィルタリングできること"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 東京 → 見つかる
        response = await client.get("/api/races", params={"venue": "東京"})
        assert response.status_code == 200
        assert len(response.json()) == 1

        # 中山 → 見つからない
        response = await client.get("/api/races", params={"venue": "中山"})
        assert response.status_code == 200
        assert len(response.json()) == 0
