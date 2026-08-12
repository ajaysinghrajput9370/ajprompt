import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker


# ==========================================
# DATABASE URL
# ==========================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable set nahi hai."
    )


# ==========================================
# DATABASE CONNECTION
# ==========================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()


# ==========================================
# PROMPT TABLE
# ==========================================

class Prompt(Base):

    __tablename__ = "prompts"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    title = Column(
        String(255),
        nullable=False
    )

    prompt = Column(
        Text,
        nullable=False
    )

    media_type = Column(
        String(20),
        nullable=False,
        default="image"
    )

    media_url = Column(
        String(500),
        nullable=True
    )

    category = Column(
        String(100),
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ==========================================
# CREATE TABLES
# ==========================================

def init_db():
    Base.metadata.create_all(bind=engine)
