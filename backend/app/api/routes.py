"""
レース関連APIエンドポイント
"""

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas import (
    EntryResponse,
    HorseResponse,
    RaceDetailResponse,
    RaceListItem,
    ScrapeRaceRequest,
    ScrapeRequest,
    ScrapeResponse,
    HorseAnalysisResponse,
)
from app.core.database import get_db
from app.models import Horse, Race, RaceEntry
from app.scraper.service import ScraperService
from app.predictor.logic import determine_running_style

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_races(
    request: ScrapeRequest,
    session: AsyncSession = Depends(get_db),
) -> ScrapeResponse:
    """指定日のレースデータを収集する"""
    service = ScraperService(session)
    try:
        result = await service.scrape_date(request.date)
        return ScrapeResponse(
            total=int(result["total"]),
            new=int(result["new"]),
            skipped=int(result["skipped"]),
            errors=int(result["errors"]),
            race_ids=list(result["race_ids"]),  # type: ignore[arg-type]
        )
    finally:
        await service.close()


@router.post("/scrape/race", response_model=ScrapeResponse)
async def scrape_single_race(
    request: ScrapeRaceRequest,
    session: AsyncSession = Depends(get_db),
) -> ScrapeResponse:
    """単一レースのデータを収集する"""
    service = ScraperService(session)
    try:
        race = await service.scrape_race(request.race_id)
        if race is None:
            return ScrapeResponse(
                total=1, new=0, skipped=1, errors=0, race_ids=[]
            )
        return ScrapeResponse(
            total=1, new=1, skipped=0, errors=0, race_ids=[request.race_id]
        )
    finally:
        await service.close()


@router.get("/races", response_model=list[RaceListItem])
async def list_races(
    date_from: date | None = Query(None, description="開始日"),
    date_to: date | None = Query(None, description="終了日"),
    venue: str | None = Query(None, description="会場名"),
    session: AsyncSession = Depends(get_db),
) -> list[RaceListItem]:
    """レース一覧を取得する"""
    stmt = select(Race).order_by(Race.date.desc(), Race.race_id)

    if date_from:
        stmt = stmt.where(Race.date >= date_from)
    if date_to:
        stmt = stmt.where(Race.date <= date_to)
    if venue:
        stmt = stmt.where(Race.venue == venue)

    result = await session.execute(stmt)
    races = result.scalars().all()

    return [
        RaceListItem(
            race_id=r.race_id,
            name=r.name,
            date=r.date,
            venue=r.venue,
            course_type=r.course_type,
            distance=r.distance,
            track_condition=r.track_condition,
            race_class=r.race_class,
            num_entries=r.num_entries,
        )
        for r in races
    ]


@router.get("/races/{race_id}", response_model=RaceDetailResponse)
async def get_race_detail(
    race_id: str,
    session: AsyncSession = Depends(get_db),
) -> RaceDetailResponse:
    """レース詳細（出走馬・結果含む）を取得する"""
    stmt = (
        select(Race)
        .where(Race.race_id == race_id)
        .options(selectinload(Race.entries).selectinload(RaceEntry.horse))
    )
    result = await session.execute(stmt)
    race = result.scalar_one_or_none()

    if race is None:
        raise HTTPException(status_code=404, detail=f"Race {race_id} not found")

    entries = [
        EntryResponse(
            horse_number=e.horse_number,
            bracket_number=e.bracket_number,
            horse=HorseResponse(
                horse_id=e.horse.horse_id,
                name=e.horse.name,
                sex=e.horse.sex,
                trainer=e.horse.trainer,
                sire=e.horse.sire,
                dam=e.horse.dam,
            ),
            jockey=e.jockey,
            weight_carried=e.weight_carried,
            odds=e.odds,
            popularity=e.popularity,
            finish_position=e.finish_position,
            finish_time=e.finish_time,
            margin=e.margin,
            passing_order=e.passing_order,
            last_3f=e.last_3f,
            horse_weight=e.horse_weight,
            horse_weight_diff=e.horse_weight_diff,
            status=e.status,
        )
        for e in sorted(race.entries, key=lambda x: x.horse_number)
    ]

    return RaceDetailResponse(
        race_id=race.race_id,
        name=race.name,
        date=race.date,
        venue=race.venue,
        course_type=race.course_type,
        distance=race.distance,
        direction=race.direction,
        weather=race.weather,
        track_condition=race.track_condition,
        race_class=race.race_class,
        num_entries=race.num_entries,
        entries=entries,
    )


@router.get("/horses/{horse_id}")
async def get_horse(
    horse_id: str,
    session: AsyncSession = Depends(get_db),
) -> HorseResponse:
    """馬の詳細情報を取得する"""
    result = await session.execute(
        select(Horse).where(Horse.horse_id == horse_id)
    )
    horse = result.scalar_one_or_none()

    if horse is None:
        raise HTTPException(status_code=404, detail=f"Horse {horse_id} not found")

    return HorseResponse(
        horse_id=horse.horse_id,
        name=horse.name,
        sex=horse.sex,
        trainer=horse.trainer,
        sire=horse.sire,
        dam=horse.dam,
    )


@router.get("/analysis/horses/{horse_id}", response_model=HorseAnalysisResponse)
async def analyze_horse_stats(
    horse_id: str,
    session: AsyncSession = Depends(get_db),
) -> HorseAnalysisResponse:
    """馬の傾向分析（脚質など）を取得する"""
    # 馬情報を取得
    stmt = select(Horse).where(Horse.horse_id == horse_id)
    result = await session.execute(stmt)
    horse = result.scalar_one_or_none()
    
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found")

    # 過去レースの出走結果を取得 (新しい順)
    async def _get_entries():
        entry_stmt = (
            select(RaceEntry)
            .where(RaceEntry.horse_id == horse.id)
            .join(Race)
            .options(selectinload(RaceEntry.race))
            .order_by(Race.date.desc())
        )
        entry_result = await session.execute(entry_stmt)
        return entry_result.scalars().all()

    entries = await _get_entries()

    # 履歴が1件以下（現レースのみ等）の場合は、自動的にスクレイプを試みる
    if len(entries) <= 1:
        logger.info("Insufficient data for horse %s (%s), scraping history...", horse.horse_id, horse.name)
        service = ScraperService(session)
        try:
            await service.scrape_horse_history(horse.horse_id)
            # スクレイプ後に再取得
            # session をリフレッシュする必要があるかもしれないが、一旦再検索で試す
            entries = await _get_entries()
        except Exception as e:
            logger.warning("Failed to scrape horse history for %s: %s", horse.horse_id, str(e))
        finally:
            await service.close()

    # 脚質判定
    style = determine_running_style(entries)
    
    # 簡易スタッツ計算 (TODO: 機械学習モデルへの置き換え)
    # スピード: 上がり3Fの平均からざっくりスコア化 (小さい方が速い)
    last_3f_list = [e.last_3f for e in entries if e.last_3f]
    avg_3f = sum(last_3f_list) / len(last_3f_list) if last_3f_list else 36.0
    # 33.0秒 -> 100点, 40.0秒 -> 30点 くらいの線形変換
    speed_score = max(30.0, min(100.0, 100.0 - (avg_3f - 33.0) * 10))

    return HorseAnalysisResponse(
        horse_id=horse.horse_id,
        name=horse.name,
        style=style.value,
        stats={
            "speed": float(f"{speed_score:.1f}"),
            "stamina": 80.0,  # 仮
            "start_dash": 75.0,  # 仮
            "races_count": float(len(entries)),
        },
    )
