import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from models.base import Base

class DatabaseConfig:
    def __init__(self):
        self.database_url = self._construct_database_url()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def _construct_database_url(self):
        """Construct PostgreSQL URL from environment variables"""
        host = os.getenv('DB_HOST', '127.0.0.1')
        port = os.getenv('DB_PORT', '5432')
        username = os.getenv('DB_USERNAME', 'netpilot_user')
        password = os.getenv('DB_PASSWORD')
        database = os.getenv('DB_NAME', 'netpilot_db')
        
        if not password:
            raise ValueError("DB_PASSWORD environment variable must be set")
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def _create_engine(self):
        """Create SQLAlchemy engine with PostgreSQL optimizations"""
        return create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before use
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true'  # SQL logging
        )
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()

# Create global database instance
db = DatabaseConfig() 