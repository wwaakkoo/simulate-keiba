"""
馬 (Horse) テーブルモデル

馬の基本情報・血統を保持する。
複数レースに出走するため、RaceEntry から参照される。
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Horse(Base):
    """馬情報テーブル"""

    __tablename__ = "horses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # netkeiba の馬ID（例: "2021104567"）
    horse_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # 基本情報
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sex: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "牡", "牝", "セ"
    birthday: Mapped[str | None] = mapped_column(String(10), nullable=True)  # "2020年3月15日"
    trainer: Mapped[str | None] = mapped_column(String(50), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 血統（予測に重要：距離適性・馬場適性の傾向）
    sire: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 父
    dam: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 母
    sire_of_dam: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 母父

    # リレーション
    entries: Mapped[list["RaceEntry"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "RaceEntry", back_populates="horse"
    )

    def __repr__(self) -> str:
        return f"<Horse(horse_id={self.horse_id}, name={self.name})>"
