from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from database import SessionLocal, engine, Loan, init_db
from logic import calculate_monthly_discount_rate, calculate_cdb_monthly_return, get_recommendation

# Initialize Database
init_db()

app = FastAPI(title="Debt Management API")

# CORS - Allow all origins including file://
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models
class LoanCreate(BaseModel):
    name: str
    creditor: str
    monthly_payment: float
    total_installments: int
    remaining_installments: int
    prepayment_value: float
    selic_rate: float
    cdi_rate: float

class LoanResponse(LoanCreate):
    id: int
    discount_monthly_percent: float
    cdb_monthly_return: float
    recommendation: str
    total_potential_economy: float

    class Config:
        orm_mode = True

# Routes
@app.post("/loans", response_model=LoanResponse)
def create_loan(loan: LoanCreate, db: Session = Depends(get_db)):
    db_loan = Loan(**loan.dict())
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    
    # Calculate computed fields for response
    discount_rate = calculate_monthly_discount_rate(db_loan.monthly_payment, db_loan.prepayment_value)
    cdb_return = calculate_cdb_monthly_return(db_loan.cdi_rate)
    recommendation = get_recommendation(discount_rate, cdb_return)
    discount_abs = db_loan.monthly_payment - db_loan.prepayment_value
    total_economy = discount_abs * db_loan.remaining_installments

    return {
        **db_loan.__dict__,
        "discount_monthly_percent": discount_rate,
        "cdb_monthly_return": cdb_return,
        "recommendation": recommendation,
        "total_potential_economy": total_economy
    }

@app.get("/loans", response_model=List[LoanResponse])
def read_loans(db: Session = Depends(get_db)):
    loans = db.query(Loan).all()
    results = []
    for loan in loans:
        discount_rate = calculate_monthly_discount_rate(loan.monthly_payment, loan.prepayment_value)
        cdb_return = calculate_cdb_monthly_return(loan.cdi_rate)
        recommendation = get_recommendation(discount_rate, cdb_return)
        discount_abs = loan.monthly_payment - loan.prepayment_value
        total_economy = discount_abs * loan.remaining_installments
        
        results.append({
            **loan.__dict__,
            "discount_monthly_percent": discount_rate,
            "cdb_monthly_return": cdb_return,
            "recommendation": recommendation,
            "total_potential_economy": total_economy
        })
    return results

@app.get("/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    loans = db.query(Loan).all()
    total_economy = 0
    total_debt = 0
    
    for loan in loans:
        discount_abs = loan.monthly_payment - loan.prepayment_value
        total_economy += discount_abs * loan.remaining_installments
        total_debt += loan.monthly_payment * loan.remaining_installments
        
    return {
        "total_potential_economy": total_economy,
        "total_outstanding_debt": total_debt,
        "loan_count": len(loans)
    }

@app.post("/simulate")
def simulate_loan(loan: LoanCreate):
    discount_rate = calculate_monthly_discount_rate(loan.monthly_payment, loan.prepayment_value)
    cdb_return = calculate_cdb_monthly_return(loan.cdi_rate)
    recommendation = get_recommendation(discount_rate, cdb_return)
    discount_abs = loan.monthly_payment - loan.prepayment_value
    total_economy = discount_abs * loan.remaining_installments
    
    return {
        "discount_monthly_percent": discount_rate,
        "cdb_monthly_return": cdb_return,
        "recommendation": recommendation,
        "total_potential_economy": total_economy,
        "payoff_amount": loan.prepayment_value * loan.remaining_installments # Simplified payoff
    }
