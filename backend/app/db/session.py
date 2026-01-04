from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Get the URL from settings (auto-switches based on TIER)
SQLALCHEMY_DATABASE_URL = settings.SWAP_DATABASE_URL

check_same_thread = False
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    check_same_thread = True
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args=connect_args
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
