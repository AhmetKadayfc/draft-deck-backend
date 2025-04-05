from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection settings from environment variables
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("FLASK_ENV") == "development"
)

# Create session factory
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create scoped session for thread safety
db_session = scoped_session(SessionFactory)

# Base class for all models
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    """Initialize database and create all tables"""
    # Import all models here to ensure they are registered with Base
    from .models.user_model import UserModel
    from .models.thesis_model import ThesisModel
    from .models.feedback_model import FeedbackModel

    # Create tables
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Get a database session"""
    session = db_session()
    try:
        yield session
    finally:
        session.close()
