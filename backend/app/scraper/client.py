"""
HTTPクライアント

netkeiba.com へのHTTPリクエストを管理する。
レート制限・リトライ・エラーハンドリングを担当。
"""

import asyncio
import logging
import random

import httpx

from app.scraper import (
    MAX_RETRIES,
    NETKEIBA_BASE_URL,
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
    REQUEST_TIMEOUT,
    USER_AGENT,
)

logger = logging.getLogger(__name__)


class ScraperClient:
    """netkeiba.com 用HTTPクライアント"""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """HTTPクライアントを取得（遅延初期化）"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept-Language": "ja",
                },
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """クライアントを閉じる"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def fetch_page(self, url: str) -> str:
        """
        ページのHTMLを取得する。

        レート制限とリトライを自動的に適用する。

        Args:
            url: 取得するURL

        Returns:
            HTMLの文字列

        Raises:
            httpx.HTTPError: リトライ後も取得に失敗した場合
        """
        client = await self._get_client()

        for attempt in range(MAX_RETRIES):
            try:
                # レート制限: ランダムな待機時間
                if attempt > 0:
                    wait = random.uniform(REQUEST_DELAY_MIN * 2, REQUEST_DELAY_MAX * 2)
                else:
                    wait = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
                await asyncio.sleep(wait)

                response = await client.get(url)
                response.raise_for_status()

                # netkeiba.com は EUC-JP が多いが、ヘッダーに含まれないこともある
                # まず EUC-JP でのデコードを試みる
                try:
                    return response.content.decode("euc-jp")
                except UnicodeDecodeError:
                    # 失敗したら UTF-8、それもだめなら httpx の推定に任せる
                    try:
                        return response.content.decode("utf-8")
                    except UnicodeDecodeError:
                        return response.text

            except httpx.HTTPStatusError as e:
                logger.warning(
                    "HTTP %d: %s (attempt %d/%d)",
                    e.response.status_code,
                    url,
                    attempt + 1,
                    MAX_RETRIES,
                )
                if attempt == MAX_RETRIES - 1:
                    raise
            except httpx.RequestError as e:
                logger.warning(
                    "Request error: %s for %s (attempt %d/%d)",
                    str(e),
                    url,
                    attempt + 1,
                    MAX_RETRIES,
                )
                if attempt == MAX_RETRIES - 1:
                    raise

        # ここには到達しないはずだが、型安全のため
        msg = f"Failed to fetch {url} after {MAX_RETRIES} retries"
        raise httpx.RequestError(msg)

    async def fetch_race_result(self, race_id: str) -> str:
        """レース結果ページのHTMLを取得する"""
        url = f"{NETKEIBA_BASE_URL}/race/{race_id}/"
        return await self.fetch_page(url)

    async def fetch_race_list(self, date_str: str) -> str:
        """
        指定日のレース一覧ページのHTMLを取得する。

        Args:
            date_str: "YYYYMMDD" 形式の日付文字列
        """
        # db.netkeiba.com の形式を使用
        url = f"{NETKEIBA_BASE_URL}/race/list/{date_str}/"
        return await self.fetch_page(url)

    async def fetch_horse_page(self, horse_id: str) -> str:
        """馬のプロフィール（過去成績）ページのHTMLを取得する"""
        # 「戦績」ページには必ず過去のレース結果テーブルが含まれる
        url = f"{NETKEIBA_BASE_URL}/horse/result/{horse_id}/"
        return await self.fetch_page(url)
