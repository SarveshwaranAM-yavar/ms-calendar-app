from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DATABASE_URL  # Ensure this exists and is correct

# Step 1: Set up SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Step 2: Define the Base class for ORM models
Base = declarative_base()

# Step 3: Define your model(s)
class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=False)

# Optional: Dependency override for FastAPI (if using)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Step 4: Run table creation if script is run directly
# def create_db_and_tables():
#     print("Attempting to create database tables...")
#     try:
#         print("Model registered:", Token.__tablename__)
#         print("Known tables before creation:", Base.metadata.tables.keys())
#         Base.metadata.create_all(bind=engine)
#         print("✅ Tables created successfully.")
#     except Exception as e:
#         print(f"❌ Error creating tables: {e}")

# if __name__ == "__main__":
#     create_db_and_tables()
