from sqlalchemy import Column, Integer, String, BLOB, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import settings

Base = declarative_base()
engine = settings.engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class DetectionHistory(Base):
    __tablename__ = "detection_history"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String, index=True)
    source_path = Column(String)
    detected_image = Column(BLOB)
    timestamp = Column(DateTime, default=datetime.now)  # Added timestamp field

Base.metadata.create_all(bind=engine)