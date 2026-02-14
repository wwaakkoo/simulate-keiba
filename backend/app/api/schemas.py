"""
Pydanticスキーマ（APIのリクエスト/レスポンス型）
"""

from datetime import date

from pydantic import BaseModel, Field

# === リクエスト ===


class ScrapeRequest(BaseModel):
    """スクレイプリクエスト"""

    date: str = Field(..., pattern=r"^\d{8}$", description="日付 (YYYYMMDD形式)")


class ScrapeRaceRequest(BaseModel):
    """単一レースのスクレイプリクエスト"""

    race_id: str = Field(..., pattern=r"^\d{12}$", description="レースID (12桁)")


# === レスポンス ===


class ScrapeResponse(BaseModel):
    """スクレイプ結果"""

    total: int
    new: int
    skipped: int
    errors: int
    race_ids: list[str]


class HorseResponse(BaseModel):
    """馬情報レスポンス"""

    horse_id: str
    name: str
    sex: str | None = None
    trainer: str | None = None
    sire: str | None = None
    dam: str | None = None

    class Config:
        from_attributes = True


class EntryResponse(BaseModel):
    """出走記録レスポンス"""

    horse_number: int
    bracket_number: int | None = None
    horse: HorseResponse
    jockey: str | None = None
    weight_carried: float | None = None
    odds: float | None = None
    popularity: int | None = None
    finish_position: int | None = None
    finish_time: str | None = None
    margin: str | None = None
    passing_order: str | None = None
    last_3f: float | None = None
    horse_weight: int | None = None
    horse_weight_diff: int | None = None
    status: str = "result"


class RaceListItem(BaseModel):
    """レース一覧の各レース"""

    race_id: str
    name: str
    date: date
    venue: str
    course_type: str
    distance: int
    track_condition: str | None = None
    race_class: str | None = None
    num_entries: int | None = None


class RaceDetailResponse(BaseModel):
    """レース詳細レスポンス"""

    race_id: str
    name: str
    date: date
    venue: str
    course_type: str
    distance: int
    direction: str | None = None
    weather: str | None = None
    track_condition: str | None = None
    race_class: str | None = None
    num_entries: int | None = None
    entries: list[EntryResponse] = []


class HorseAnalysisResponse(BaseModel):
    horse_id: str
    name: str = ""
    style: str  # NIGE, SENKO, SASHI, OIKOMI, UNKNOWN
    stats: dict[str, float]  # speed, stamina, etc.


class PredictionItem(BaseModel):
    """各馬の予測結果"""
    horse_name: str
    horse_number: int
    predicted_position: float
    predicted_rank: int
    mark: str


class PredictionResponse(BaseModel):
    """予測APIレスポンス"""
    race_id: str
    predictions: list[PredictionItem]
    model_version: str
    method: str
