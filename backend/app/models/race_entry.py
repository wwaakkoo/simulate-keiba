"""
出走記録 (RaceEntry) テーブルモデル

Race と Horse を結ぶ中間テーブル。
出走情報（枠番・騎手等）とレース結果（着順・タイム等）の両方を保持する。

予測エンジンの主要な特徴量ソースであり、
シミュレーションのアニメーションデータソースでもある。
"""

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.horse import Horse
from app.models.race import Race


class RaceEntry(Base):
    """出走記録・結果テーブル"""

    __tablename__ = "race_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 外部キー
    race_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("races.id", ondelete="CASCADE"), nullable=False
    )
    horse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("horses.id"), nullable=False
    )

    # === 出走情報（レース前に確定するデータ） ===

    bracket_number: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 枠番 (1-8)
    horse_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 馬番 (1-18)
    jockey: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 騎手名
    weight_carried: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # 斤量 (kg): 1kg ≒ 1馬身分の影響

    # === レース前のマーケットデータ ===

    odds: Mapped[float | None] = mapped_column(Float, nullable=True)  # 単勝オッズ
    popularity: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 人気順

    # === レース結果（レース後に確定するデータ） ===

    finish_position: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 着順（予測対象）
    finish_time: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # 走破タイム（例: "1:33.5"）
    margin: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # 着差（例: "1/2", "クビ", "アタマ"）→ シミュレーションのゴール間隔に使用

    # === シミュレーション用データ ===

    passing_order: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # 通過順（例: "3-3-2-1"）→ レース中の位置変動アニメーションに使用
    last_3f: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # 上がり3F（秒）→ ラストスパートの速度変化に使用

    # === コンディションデータ ===

    horse_weight: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 馬体重 (kg)
    horse_weight_diff: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 馬体重増減 (kg)

    # === リレーション ===

    race: Mapped["Race"] = relationship("Race", back_populates="entries")
    horse: Mapped["Horse"] = relationship("Horse", back_populates="entries")

    # 同じレースに同じ馬が2度出走することはない
    __table_args__ = (
        UniqueConstraint("race_id", "horse_id", name="uq_race_horse"),
    )

    def __repr__(self) -> str:
        return (
            f"<RaceEntry(race_id={self.race_id}, horse_number={self.horse_number}, "
            f"position={self.finish_position})>"
        )
