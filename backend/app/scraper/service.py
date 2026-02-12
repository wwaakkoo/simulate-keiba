"""
スクレイパーサービス

HTTPクライアント、HTMLパーサー、DB保存を統合する。
外部公開されるメインインターフェース。
"""

import logging
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Horse, Race, RaceEntry
from app.scraper.client import ScraperClient
from app.scraper.parser import ParsedRacePage, parse_race_list_page, parse_race_result_page

logger = logging.getLogger(__name__)


class ScraperService:
    """レースデータの収集・保存サービス"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._client = ScraperClient()

    async def close(self) -> None:
        """クライアントをクリーンアップ"""
        await self._client.close()

    async def scrape_date(self, target_date: str) -> dict[str, int | list[str]]:
        """
        指定日の全レースデータを収集・保存する。

        Args:
            target_date: "YYYYMMDD" 形式の日付文字列

        Returns:
            収集結果のサマリー
        """
        logger.info("Scraping races for date: %s", target_date)

        # 1. レースID一覧を取得
        list_html = await self._client.fetch_race_list(target_date)
        race_ids = parse_race_list_page(list_html)

        if not race_ids:
            logger.info("No races found for date: %s", target_date)
            return {"total": 0, "new": 0, "skipped": 0, "errors": 0, "race_ids": []}

        logger.info("Found %d races for %s", len(race_ids), target_date)

        new_count = 0
        skipped_count = 0
        error_count = 0
        saved_ids: list[str] = []

        # 2. 各レースの詳細を取得
        for race_id in race_ids:
            try:
                # 既存チェック
                existing = await self._session.execute(
                    select(Race).where(Race.race_id == race_id)
                )
                if existing.scalar_one_or_none() is not None:
                    logger.debug("Race %s already exists, skipping", race_id)
                    skipped_count += 1
                    continue

                # レース結果をスクレイプ
                result_html = await self._client.fetch_race_result(race_id)
                parsed = parse_race_result_page(result_html, race_id)

                # DBに保存
                await self._save_race(parsed)
                new_count += 1
                saved_ids.append(race_id)
                logger.info("Saved race: %s (%s)", race_id, parsed.race_info.name)

            except Exception:
                error_count += 1
                logger.exception("Error scraping race %s", race_id)
                continue

        await self._session.commit()

        return {
            "total": len(race_ids),
            "new": new_count,
            "skipped": skipped_count,
            "errors": error_count,
            "race_ids": saved_ids,
        }

    async def scrape_race(self, race_id: str) -> Race | None:
        """
        単一レースのデータを収集・保存する。

        Args:
            race_id: netkeiba のレースID

        Returns:
            保存したRaceオブジェクト、または既存の場合はNone
        """
        # 既存チェック
        existing = await self._session.execute(
            select(Race).where(Race.race_id == race_id)
        )
        if existing.scalar_one_or_none() is not None:
            logger.info("Race %s already exists", race_id)
            return None

        result_html = await self._client.fetch_race_result(race_id)
        parsed = parse_race_result_page(result_html, race_id)
        race = await self._save_race(parsed)
        await self._session.commit()

        return race

    async def scrape_horse_history(self, horse_id: str) -> Horse | None:
        """
        馬の過去成績を収集・保存する。

        Args:
            horse_id: netkeiba の馬ID
        """
        logger.info("Scraping horse history for: %s", horse_id)
        
        html = await self._client.fetch_horse_page(horse_id)
        from app.scraper.parser import parse_horse_page
        parsed = parse_horse_page(html, horse_id)

        # 馬を取得 or 作成
        result = await self._session.execute(
            select(Horse).where(Horse.horse_id == horse_id)
        )
        horse = result.scalar_one_or_none()
        if not horse:
            horse = Horse(
                horse_id=horse_id,
                name=parsed.name,
                sex=parsed.sex,
                trainer=parsed.trainer,
                sire=parsed.sire,
                dam=parsed.dam
            )
            self._session.add(horse)
            await self._session.flush()
        else:
            # 情報を更新
            horse.trainer = parsed.trainer
            horse.sire = parsed.sire
            horse.dam = parsed.dam

        # 過去成績を保存
        for h_entry in parsed.history:
            # レースをチェック
            r_result = await self._session.execute(
                select(Race).where(Race.race_id == h_entry.race_id)
            )
            race = r_result.scalar_one_or_none()
            if not race:
                # スタブとして作成
                race_date = datetime.strptime(h_entry.date, "%Y-%m-%d").date()
                race = Race(
                    race_id=h_entry.race_id,
                    name=h_entry.race_name,
                    date=race_date,
                    venue=h_entry.venue,
                    course_type=h_entry.course_type,
                    distance=h_entry.distance,
                    track_condition=h_entry.track_condition,
                    num_entries=0 # 不明だが一旦0
                )
                self._session.add(race)
                await self._session.flush()

            # 出走記録をチェック
            e_result = await self._session.execute(
                select(RaceEntry)
                .where(RaceEntry.race_id == race.id)
                .where(RaceEntry.horse_id == horse.id)
            )
            if e_result.scalar_one_or_none() is None:
                entry = RaceEntry(
                    race_id=race.id,
                    horse_id=horse.id,
                    bracket_number=h_entry.bracket_number,
                    horse_number=h_entry.horse_number,
                    jockey=h_entry.jockey,
                    weight_carried=h_entry.weight_carried,
                    odds=h_entry.odds,
                    popularity=h_entry.popularity,
                    finish_position=h_entry.finish_position,
                    finish_time=h_entry.finish_time,
                    margin=h_entry.margin,
                    passing_order=h_entry.passing_order,
                    last_3f=h_entry.last_3f,
                    horse_weight=h_entry.horse_weight,
                    horse_weight_diff=h_entry.horse_weight_diff,
                    status=h_entry.status
                )
                self._session.add(entry)

        await self._session.commit()
        return horse

    async def _save_race(self, parsed: ParsedRacePage) -> Race:
        """パース済みデータをDBに保存する"""
        info = parsed.race_info

        # 日付文字列を date オブジェクトに変換
        race_date = datetime.strptime(info.date, "%Y-%m-%d").date() if info.date else date.today()

        # Race レコード作成
        race = Race(
            race_id=info.race_id,
            name=info.name,
            date=race_date,
            venue=info.venue,
            course_type=info.course_type,
            distance=info.distance,
            direction=info.direction,
            weather=info.weather,
            track_condition=info.track_condition,
            race_class=info.race_class,
            num_entries=info.num_entries,
        )
        self._session.add(race)
        await self._session.flush()  # race.id を確定

        # 各出走馬を保存
        for entry_data in parsed.entries:
            # Horse を取得 or 作成
            horse = await self._get_or_create_horse(entry_data)

            # RaceEntry を作成
            entry = RaceEntry(
                race_id=race.id,
                horse_id=horse.id,
                bracket_number=entry_data.bracket_number,
                horse_number=entry_data.horse_number,
                jockey=entry_data.jockey,
                weight_carried=entry_data.weight_carried,
                odds=entry_data.odds,
                popularity=entry_data.popularity,
                finish_position=entry_data.finish_position,
                finish_time=entry_data.finish_time,
                margin=entry_data.margin,
                passing_order=entry_data.passing_order,
                last_3f=entry_data.last_3f,
                horse_weight=entry_data.horse_weight,
                horse_weight_diff=entry_data.horse_weight_diff,
                status=entry_data.status,
            )
            self._session.add(entry)

        return race

    async def _get_or_create_horse(self, entry_data: "ParsedEntryResult") -> Horse:  # type: ignore[name-defined]  # noqa: F821
        """馬を取得、なければ作成する"""
        from app.scraper.parser import ParsedEntryResult as _PE  # noqa: F811

        assert isinstance(entry_data, _PE)

        if entry_data.horse_id:
            result = await self._session.execute(
                select(Horse).where(Horse.horse_id == entry_data.horse_id)
            )
            horse = result.scalar_one_or_none()
            if horse:
                return horse

        # 性別を分離
        sex = None
        if entry_data.sex_age:
            sex = entry_data.sex_age[0] if entry_data.sex_age else None

        horse = Horse(
            horse_id=entry_data.horse_id or f"unknown_{entry_data.horse_name}",
            name=entry_data.horse_name,
            sex=sex,
            trainer=entry_data.trainer,
        )
        self._session.add(horse)
        await self._session.flush()

        return horse
