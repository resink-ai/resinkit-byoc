from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from resinkit_api.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False}, echo=settings.SQLALCHEMY_ECHO)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
