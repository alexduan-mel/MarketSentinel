from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    provider: str = Field(..., description="Source provider name (e.g., 'finnhub', 'yahoo_rss')")
    title: str = Field(..., description="Article headline")
    url: str = Field(..., description="Article URL")
    published_at: datetime = Field(..., description="Publication timestamp")
    summary: Optional[str] = Field(None, description="Article summary or snippet")
    symbols: list[str] = Field(default_factory=list, description="Related ticker symbols")
    sentiment: Optional[str] = Field(None, description="Sentiment classification if available")
    source: Optional[str] = Field(None, description="Original source name (e.g., 'Reuters', 'Bloomberg')")
