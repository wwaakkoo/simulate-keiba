"""
レース (Race) テーブルモデル

1レースの基本情報を保持する。
"""

from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Race(Base):
    """レース情報テーブル"""

    __tablename__ = "races"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # netkeiba のレースID（例: "202506010101"）
    race_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # レース基本情報
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    venue: Mapped[str] = mapped_column(String(20), nullable=False)  # 例: "東京", "中山"

    # コース情報
    course_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "芝" or "ダート"
    distance: Mapped[int] = mapped_column(Integer, nullable=False)  # メートル
    direction: Mapped[str] = mapped_column(String(10), nullable=True)  # "右" or "左" or "直線"

    # コンディション
    weather: Mapped[str | None] = mapped_column(String(10), nullable=True)  # "晴", "曇", "雨" etc.
    track_condition: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # "良", "稍重", "重", "不良"

    # レースクラス
    race_class: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # "G1", "G2", "3勝クラス" etc.

    # 出走頭数
    num_entries: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # リレーション
    entries: Mapped[list["RaceEntry"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "RaceEntry", back_populates="race", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Race(race_id={self.race_id}, name={self.name}, date={self.date})>"
