from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, DECIMAL, ARRAY, func
from src.storage.database import Base


class NewsData(Base):
    __tablename__ = "news_data"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    content = Column(Text)
    source = Column(String(200))
    url = Column(Text)
    published_at = Column(TIMESTAMP, nullable=False, index=True)
    sentiment_score = Column(DECIMAL(3, 2))
    coins = Column(ARRAY(String))
    created_at = Column(TIMESTAMP, server_default=func.now())
