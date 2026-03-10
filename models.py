import os
import re
import hashlib
from datetime import datetime
from typing import List
from uuid import uuid4
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base, relationship, Session, sessionmaker
from sqlalchemy import create_engine

# ------------------------------------------------------------
# Database URL handling with auto‑fixes and SSL configuration
# ------------------------------------------------------------
raw_db_url = os.getenv("DATABASE_URL", os.getenv("POSTGRES_URL", "sqlite:///./app.db"))
if raw_db_url.startswith("postgresql+asyncpg://"):
    raw_db_url = raw_db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
elif raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg://")

# Determine if we are using a non‑local PostgreSQL instance (i.e., not SQLite)
use_ssl = not raw_db_url.startswith("sqlite") and "localhost" not in raw_db_url and "127.0.0.1" not in raw_db_url
engine_kwargs = {"connect_args": {"sslmode": "require"}} if use_ssl else {}
engine = create_engine(raw_db_url, future=True, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()

# ------------------------------------------------------------
# Helper: URL hash for deduplication
# ------------------------------------------------------------
def _hash_url(url: str) -> str:
    # Normalise by stripping whitespace and lower‑casing
    norm = url.strip().lower()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()

# ------------------------------------------------------------
# SQLAlchemy models – table names prefixed with "bb_"
# ------------------------------------------------------------
class Bookmark(Base):
    __tablename__ = "bb_bookmarks"
    __table_args__ = (
        UniqueConstraint("hash", name="uq_bb_bookmarks_hash"),
        Index("idx_bb_bookmarks_hash", "hash"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    hash = Column(String, nullable=False)
    summary = Column(String, nullable=True)

    # Relationships
    tags = relationship("Tag", back_populates="bookmark", cascade="all, delete-orphan")
    ai_predictions = relationship("AIPrediction", back_populates="bookmark", cascade="all, delete-orphan")

    def __init__(self, url: str, title: str, **kwargs):
        super().__init__(url=url, title=title, hash=_hash_url(url), **kwargs)

class Tag(Base):
    __tablename__ = "bb_tags"
    __table_args__ = (
        UniqueConstraint("bookmark_id", "tag_name", name="uq_bb_tags_bookmark_tag"),
        Index("idx_bb_tags_tag_name", "tag_name"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    bookmark_id = Column(String, ForeignKey("bb_bookmarks.id"), nullable=False)
    tag_name = Column(String, nullable=False)
    is_ai_generated = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    bookmark = relationship("Bookmark", back_populates="tags")

class AIPrediction(Base):
    __tablename__ = "bb_ai_predictions"
    __table_args__ = (
        Index("idx_bb_ai_predictions_bookmark", "bookmark_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    bookmark_id = Column(String, ForeignKey("bb_bookmarks.id"), nullable=False)
    model_version = Column(String, nullable=False)
    generated_tags = Column(JSON, nullable=False)  # list of strings
    confidence_score = Column(String, nullable=False)  # stored as string to avoid float precision issues
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    bookmark = relationship("Bookmark", back_populates="ai_predictions")

# ------------------------------------------------------------
# Pydantic schemas for request/response payloads
# ------------------------------------------------------------
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class BookmarkCreate(BaseModel):
    url: HttpUrl

class BookmarkOut(BaseModel):
    id: str
    title: str
    url: HttpUrl
    tags: List[str] = []
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

class TagOut(BaseModel):
    tag_name: str
    is_ai_generated: bool

    class Config:
        orm_mode = True

class ExportItem(BaseModel):
    id: str
    title: str
    url: HttpUrl
    tags: List[str]
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

# Utility function to get a DB session for FastAPI dependency injection
from fastapi import Depends

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
