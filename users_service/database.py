from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

url_database = "sqlite:///./users.db"

engine = create_engine(url_database, connect_args={"check_same_thread": False})

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)  
Base = declarative_base()

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()