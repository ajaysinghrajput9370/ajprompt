# ==========================================
# database.py - Render Disk Support
# ==========================================

import os
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
    media_type = Column(String(50), default="image")
    media_url = Column(String(500), nullable=False)
    status = Column(String(50), default="published")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Prompt(id={self.id}, title={self.title})>"

# Database setup - Render Disk support
def get_database_url():
    # Render Disk path
    render_db_path = "/var/lib/database/database.db"
    
    # Agar Render Disk available hai toh use karein
    if os.path.exists("/var/lib/database") or os.getenv("RENDER"):
        # Render par hai
        db_dir = "/var/lib/database"
        os.makedirs(db_dir, exist_ok=True)
        return f"sqlite:///{os.path.join(db_dir, 'database.db')}"
    
    # Local development
    return "sqlite:///database.db"

DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Create tables if they don't exist"""
    Base.metadata.create_all(engine)
