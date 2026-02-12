"""
DBモデルのテスト

Race, Horse, RaceEntry のCRUD操作をテストする。
"""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Horse, Race, RaceEntry


@pytest.mark.asyncio
async def test_create_race(db_session: AsyncSession) -> None:
    """レースの作成と取得"""
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
        num_entries=16,
    )
    db_session.add(race)
    await db_session.commit()

    result = await db_session.execute(select(Race).where(Race.race_id == "202506010101"))
    saved_race = result.scalar_one()

    assert saved_race.name == "テスト記念"
    assert saved_race.venue == "東京"
    assert saved_race.distance == 2000
    assert saved_race.course_type == "芝"
    assert saved_race.track_condition == "良"


@pytest.mark.asyncio
async def test_create_horse(db_session: AsyncSession) -> None:
    """馬の作成と取得"""
    horse = Horse(
        horse_id="2021104567",
        name="テストディープ",
        sex="牡",
        birthday="2021年3月15日",
        trainer="テスト調教師",
        sire="ディープインパクト",
        dam="テストマザー",
        sire_of_dam="キングカメハメハ",
    )
    db_session.add(horse)
    await db_session.commit()

    result = await db_session.execute(select(Horse).where(Horse.horse_id == "2021104567"))
    saved_horse = result.scalar_one()

    assert saved_horse.name == "テストディープ"
    assert saved_horse.sire == "ディープインパクト"
    assert saved_horse.sire_of_dam == "キングカメハメハ"


@pytest.mark.asyncio
async def test_create_race_entry(db_session: AsyncSession) -> None:
    """出走記録の作成とリレーション"""
    # レースと馬を作成
    race = Race(
        race_id="202506010101",
        name="テスト記念",
        date=date(2025, 6, 1),
        venue="東京",
        course_type="芝",
        distance=2000,
    )
    horse = Horse(
        horse_id="2021104567",
        name="テストディープ",
    )
    db_session.add_all([race, horse])
    await db_session.flush()

    # 出走記録を作成
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
        margin="クビ",
        passing_order="3-3-2-1",
        last_3f=33.8,
        horse_weight=468,
        horse_weight_diff=-4,
    )
    db_session.add(entry)
    await db_session.commit()

    # リレーションを通じてデータ取得
    result = await db_session.execute(
        select(RaceEntry).where(RaceEntry.race_id == race.id)
    )
    saved_entry = result.scalar_one()

    assert saved_entry.horse_number == 5
    assert saved_entry.jockey == "テスト騎手"
    assert saved_entry.finish_position == 1
    assert saved_entry.passing_order == "3-3-2-1"
    assert saved_entry.last_3f == 33.8
    assert saved_entry.margin == "クビ"


@pytest.mark.asyncio
async def test_race_entries_relationship(db_session: AsyncSession) -> None:
    """レースから出走馬のリレーションを辿れること"""
    race = Race(
        race_id="202506010101",
        name="テスト記念",
        date=date(2025, 6, 1),
        venue="東京",
        course_type="芝",
        distance=2000,
    )
    horse1 = Horse(horse_id="2021104567", name="テストディープ")
    horse2 = Horse(horse_id="2021104568", name="テストアーモンド")
    db_session.add_all([race, horse1, horse2])
    await db_session.flush()

    entry1 = RaceEntry(
        race_id=race.id,
        horse_id=horse1.id,
        horse_number=1,
        finish_position=1,
    )
    entry2 = RaceEntry(
        race_id=race.id,
        horse_id=horse2.id,
        horse_number=2,
        finish_position=2,
    )
    db_session.add_all([entry1, entry2])
    await db_session.commit()

    # リフレッシュしてリレーションをロード
    await db_session.refresh(race, ["entries"])

    assert len(race.entries) == 2
    horse_names = {e.horse_number for e in race.entries}
    assert horse_names == {1, 2}


@pytest.mark.asyncio
async def test_unique_constraint_race_horse(db_session: AsyncSession) -> None:
    """同じレースに同じ馬が重複登録できないこと"""
    race = Race(
        race_id="202506010101",
        name="テスト記念",
        date=date(2025, 6, 1),
        venue="東京",
        course_type="芝",
        distance=2000,
    )
    horse = Horse(horse_id="2021104567", name="テストディープ")
    db_session.add_all([race, horse])
    await db_session.flush()

    entry1 = RaceEntry(race_id=race.id, horse_id=horse.id, horse_number=1)
    db_session.add(entry1)
    await db_session.flush()

    # 同じ race_id + horse_id の組み合わせは重複エラー
    entry2 = RaceEntry(race_id=race.id, horse_id=horse.id, horse_number=2)
    db_session.add(entry2)

    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await db_session.flush()
