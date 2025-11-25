from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./loans.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    creditor = Column(String)
    monthly_payment = Column(Float)
    total_installments = Column(Integer)
    remaining_installments = Column(Integer)
    prepayment_value = Column(Float)
    selic_rate = Column(Float)
    cdi_rate = Column(Float)
    start_date = Column(DateTime)  # When the loan started
    monthly_due_day = Column(Integer)  # Day of month payment is due (1-31)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
