import os
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean
)

from sqlalchemy.orm import declarative_base, sessionmaker


# ==========================================
# LOCAL SQLITE DATABASE
# ==========================================

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

DATABASE_FOLDER = os.path.join(
    BASE_DIR,
    "instance"
)

os.makedirs(
    DATABASE_FOLDER,
    exist_ok=True
)

DATABASE_PATH = os.path.join(
    DATABASE_FOLDER,
    "prompts.db"
)

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# ==========================================
# DATABASE CONNECTION
# ==========================================

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
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

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ==========================================
# CREATE DATABASE TABLE
# ==========================================

def init_db():

    Base.metadata.create_all(
        bind=engine
    )
