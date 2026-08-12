-- ==========================================
-- database.py
-- ==========================================

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime


Base = declarative_base()


class Prompt(Base):
    __tablename__ = "prompts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)
    category = Column(String(100), default="funny")
    media_type = Column(String(50), default="image")  # image / video
    media_url = Column(String(500), nullable=False)
    status = Column(String(50), default="published")  # published / draft
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Prompt(id={self.id}, title={self.title})>"


# Database setup
DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create tables if they don't exist"""
    Base.metadata.create_all(engine)
