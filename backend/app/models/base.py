"""
SQLAlchemy ベースモデル

すべてのDBモデルはこのBaseを継承する。
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy宣言的ベースクラス"""

    pass
