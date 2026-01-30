from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(Text, unique=True, nullable=False)
    name = Column(Text)
    asset_type = Column(Text, default="stock")


class NewsEvent(Base):
    __tablename__ = "news_events"
    
    time = Column(TIMESTAMP(timezone=True), nullable=False, primary_key=True)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    headline = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    summary = Column(Text)
    sentiment_score = Column(Numeric)
    extra_data = Column("metadata", JSON)
