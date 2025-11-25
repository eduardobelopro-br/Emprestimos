from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from database import SessionLocal, engine, Emprestimo, init_db
from logic import calculate_monthly_discount_rate, calculate_cdb_monthly_return, get_recommendation, calculate_remaining_installments
from datetime import datetime

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
class EmprestimoCreate(BaseModel):
    descricao: str
    instituicao_credora: str
    valor_parcela: float
    qtd_total_parcelas: int
    qtd_parcelas_devidas: int
    valor_parcela_adiantada: float
    taxa_selic_registro: float
    taxa_cdi_registro: float
    data_cadastro: str  # ISO format date string
    dia_vencimento: int

class EmprestimoUpdate(BaseModel):
    valor_parcela_adiantada: float
    taxa_selic_registro: float
    taxa_cdi_registro: float
    update_date: str  # ISO format date string

class EmprestimoResponse(EmprestimoCreate):
    id: int
    discount_monthly_percent: float
    cdb_monthly_return: float
    recommendation: str
    total_potential_economy: float

    class Config:
        orm_mode = True

# Routes
@app.post("/loans", response_model=EmprestimoResponse)
def create_loan(emprestimo: EmprestimoCreate, db: Session = Depends(get_db)):
    db_emprestimo = Emprestimo(**emprestimo.dict())
    db.add(db_emprestimo)
    db.commit()
    db.refresh(db_emprestimo)
    
    # Calculate computed fields for response
    discount_rate = calculate_monthly_discount_rate(db_emprestimo.valor_parcela, db_emprestimo.valor_parcela_adiantada)
    cdb_return = calculate_cdb_monthly_return(db_emprestimo.taxa_cdi_registro)
    recommendation = get_recommendation(discount_rate, cdb_return)
    discount_abs = db_emprestimo.valor_parcela - db_emprestimo.valor_parcela_adiantada
    total_economy = discount_abs * db_emprestimo.qtd_parcelas_devidas

    return {
        **db_emprestimo.__dict__,
        "discount_monthly_percent": discount_rate,
        "cdb_monthly_return": cdb_return,
        "recommendation": recommendation,
        "total_potential_economy": total_economy
    }

@app.get("/loans", response_model=List[EmprestimoResponse])
def read_loans(db: Session = Depends(get_db)):
    emprestimos = db.query(Emprestimo).all()
    results = []
    for emprestimo in emprestimos:
        discount_rate = calculate_monthly_discount_rate(emprestimo.valor_parcela, emprestimo.valor_parcela_adiantada)
        cdb_return = calculate_cdb_monthly_return(emprestimo.taxa_cdi_registro)
        recommendation = get_recommendation(discount_rate, cdb_return)
        discount_abs = emprestimo.valor_parcela - emprestimo.valor_parcela_adiantada
        total_economy = discount_abs * emprestimo.qtd_parcelas_devidas
        
        results.append({
            **emprestimo.__dict__,
            "discount_monthly_percent": discount_rate,
            "cdb_monthly_return": cdb_return,
            "recommendation": recommendation,
            "total_potential_economy": total_economy
        })
    return results

@app.get("/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    emprestimos = db.query(Emprestimo).all()
    total_economy = 0
    total_debt = 0
    
    for emprestimo in emprestimos:
        discount_abs = emprestimo.valor_parcela - emprestimo.valor_parcela_adiantada
        total_economy += discount_abs * emprestimo.qtd_parcelas_devidas
        total_debt += emprestimo.valor_parcela * emprestimo.qtd_parcelas_devidas
        
    return {
        "total_potential_economy": total_economy,
        "total_outstanding_debt": total_debt,
        "loan_count": len(emprestimos)
    }

@app.post("/simulate")
def simulate_loan(emprestimo: EmprestimoCreate):
    discount_rate = calculate_monthly_discount_rate(emprestimo.valor_parcela, emprestimo.valor_parcela_adiantada)
    cdb_return = calculate_cdb_monthly_return(emprestimo.taxa_cdi_registro)
    recommendation = get_recommendation(discount_rate, cdb_return)
    discount_abs = emprestimo.valor_parcela - emprestimo.valor_parcela_adiantada
    total_economy = discount_abs * emprestimo.qtd_parcelas_devidas
    
    return {
        "discount_monthly_percent": discount_rate,
        "cdb_monthly_return": cdb_return,
        "recommendation": recommendation,
        "total_potential_economy": total_economy,
        "payoff_amount": emprestimo.valor_parcela_adiantada * emprestimo.qtd_parcelas_devidas
    }

@app.patch("/loans/{loan_id}", response_model=EmprestimoResponse)
def update_loan(loan_id: int, emprestimo_update: EmprestimoUpdate, db: Session = Depends(get_db)):
    db_emprestimo = db.query(Emprestimo).filter(Emprestimo.id == loan_id).first()
    if not db_emprestimo:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    # Parse update date
    update_date = datetime.fromisoformat(emprestimo_update.update_date.replace('Z', '+00:00'))
    
    # Parse data_cadastro from string to datetime
    data_cadastro = datetime.fromisoformat(db_emprestimo.data_cadastro)
    
    # Calculate remaining installments based on dates
    remaining = calculate_remaining_installments(
        data_cadastro,
        db_emprestimo.qtd_total_parcelas,
        db_emprestimo.dia_vencimento,
        update_date
    )
    
    # Update fields
    db_emprestimo.valor_parcela_adiantada = emprestimo_update.valor_parcela_adiantada
    db_emprestimo.taxa_selic_registro = emprestimo_update.taxa_selic_registro
    db_emprestimo.taxa_cdi_registro = emprestimo_update.taxa_cdi_registro
    db_emprestimo.qtd_parcelas_devidas = remaining
    
    db.commit()
    db.refresh(db_emprestimo)
    
    # Calculate computed fields for response
    discount_rate = calculate_monthly_discount_rate(db_emprestimo.valor_parcela, db_emprestimo.valor_parcela_adiantada)
    cdb_return = calculate_cdb_monthly_return(db_emprestimo.taxa_cdi_registro)
    recommendation = get_recommendation(discount_rate, cdb_return)
    discount_abs = db_emprestimo.valor_parcela - db_emprestimo.valor_parcela_adiantada
    total_economy = discount_abs * db_emprestimo.qtd_parcelas_devidas
    
    return {
        **db_emprestimo.__dict__,
        "discount_monthly_percent": discount_rate,
        "cdb_monthly_return": cdb_return,
        "recommendation": recommendation,
        "total_potential_economy": total_economy
    }
