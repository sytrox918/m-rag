from sqlalchemy import Column, String, Integer, Float, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from config.settings import settings

Base = declarative_base()

class DocumentModel(Base):
    __tablename__ = 'documents'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ContentUnitModel(Base):
    __tablename__ = 'content_units'
    
    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey('documents.id'), nullable=False)
    document_name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    
    title = Column(Text, nullable=True)
    text = Column(Text, nullable=True)
    searchable_text = Column(Text, nullable=True)
    ocr_text = Column(Text, nullable=True)
    visual_description = Column(Text, nullable=True)
    
    extraction_methods = Column(JSON, nullable=True)
    extraction_confidence = Column(JSON, nullable=True)
    parent_unit_id = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    
    equations = Column(JSON, nullable=True)
    tables = Column(JSON, nullable=True)
    topics = Column(JSON, nullable=True)
    concepts = Column(JSON, nullable=True)
    prerequisites = Column(JSON, nullable=True)
    
    page = Column(Integer, nullable=True)
    slide = Column(Integer, nullable=True)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    bbox = Column(JSON, nullable=True)
    asset_ids = Column(JSON, nullable=True)
    
    embedding = Column(Vector(1024), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AssetModel(Base):
    __tablename__ = 'assets'
    
    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey('documents.id'), nullable=False)
    file_path = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
