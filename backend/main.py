from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from database import SessionLocal, engine, Emprestimo, HistoricoValorAdiantado, init_db
from logic import calculate_monthly_discount_rate, calculate_cdb_monthly_return, get_recommendation, calculate_remaining_installments
from bacen_api import BacenAPI
from excel_handler import export_loans_to_excel, import_loans_from_excel, auto_sync_to_excel
from datetime import datetime
import os

from fastapi.staticfiles import StaticFiles
import os

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

class HistoricoCreate(BaseModel):
    data_registro: str  # ISO format date string
    valor_parcela_adiantada: float
    taxa_selic: float = None
    taxa_cdi: float = None

class HistoricoResponse(BaseModel):
    id: int
    emprestimo_id: int
    data_registro: str
    valor_parcela_adiantada: float
    taxa_selic: float = None
    taxa_cdi: float = None
    
    class Config:
        orm_mode = True

# Routes
@app.post("/loans", response_model=EmprestimoResponse)
def create_loan(emprestimo: EmprestimoCreate, db: Session = Depends(get_db)):
    db_emprestimo = Emprestimo(**emprestimo.dict())
    db.add(db_emprestimo)
    db.commit()
    db.refresh(db_emprestimo)
    
    # Sincronização automática para Excel
    auto_sync_to_excel(db)
    
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
    
    # Sincronização automática para Excel
    auto_sync_to_excel(db)
    
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

@app.get("/taxas/atuais")
def get_taxas_atuais():
    """
    Busca as taxas SELIC e CDI atuais diretamente da API do Banco Central (BACEN)
    """
    taxas = BacenAPI.buscar_taxas_atuais()
    return {
        "selic": taxas.get("selic"),
        "cdi": taxas.get("cdi"),
        "data_atualizacao": taxas.get("data_atualizacao")
    }

# Histórico de Valores Adiantados - Endpoints
@app.post("/loans/{loan_id}/historico", response_model=HistoricoResponse)
def create_historico(loan_id: int, historico: HistoricoCreate, db: Session = Depends(get_db)):
    """
    Registra um novo valor de parcela adiantada para um empréstimo em uma data específica
    """
    # Verifica se o empréstimo existe
    db_emprestimo = db.query(Emprestimo).filter(Emprestimo.id == loan_id).first()
    if not db_emprestimo:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    # Cria o histórico
    db_historico = HistoricoValorAdiantado(
        emprestimo_id=loan_id,
        **historico.dict()
    )
    db.add(db_historico)
    db.commit()
    db.refresh(db_historico)
    
    # Sincronização automática para Excel
    auto_sync_to_excel(db)
    
    return db_historico

@app.get("/loans/{loan_id}/historico", response_model=List[HistoricoResponse])
def get_loan_historico(loan_id: int, db: Session = Depends(get_db)):
    """
    Busca todos os registros históricos de um empréstimo específico
    """
    db_emprestimo = db.query(Emprestimo).filter(Emprestimo.id == loan_id).first()
    if not db_emprestimo:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    historicos = db.query(HistoricoValorAdiantado).filter(
        HistoricoValorAdiantado.emprestimo_id == loan_id
    ).order_by(HistoricoValorAdiantado.data_registro).all()
    
    return historicos

@app.get("/historico/all")
def get_all_historico(db: Session = Depends(get_db)):
    """
    Busca todos os históricos de todos os empréstimos para gerar o gráfico de evolução
    Retorna dados agrupados por empréstimo
    """
    emprestimos = db.query(Emprestimo).all()
    result = []
    
    for emprestimo in emprestimos:
        historicos = db.query(HistoricoValorAdiantado).filter(
            HistoricoValorAdiantado.emprestimo_id == emprestimo.id
        ).order_by(HistoricoValorAdiantado.data_registro).all()
        
        if historicos:  # Só inclui se houver histórico
            result.append({
                "emprestimo_id": emprestimo.id,
                "emprestimo_nome": emprestimo.descricao,
                "historicos": [
                    {
                        "data_registro": h.data_registro,
                        "valor_parcela_adiantada": h.valor_parcela_adiantada,
                        "taxa_selic": h.taxa_selic,
                        "taxa_cdi": h.taxa_cdi
                    } for h in historicos
                ]
            })
    
    return result


# Excel Export/Import Endpoints
@app.get("/export/excel")
def export_to_excel(db: Session = Depends(get_db)):
    """
    Exporta todos os empréstimos e histórico para arquivo Excel
    """
    try:
        emprestimos = db.query(Emprestimo).all()
        historicos = db.query(HistoricoValorAdiantado).all()
        
        file_path = export_loans_to_excel(emprestimos, historicos)
        
        return FileResponse(
            path=file_path,
            filename="emprestimos_backup.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao exportar para Excel: {str(e)}")


@app.post("/import/excel")
async def import_from_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Importa empréstimos e histórico de arquivo Excel
    """
    try:
        # Salvar arquivo temporariamente
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Importar dados
        result = import_loans_from_excel(temp_file_path, db)
        
        # Remover arquivo temporário
        os.remove(temp_file_path)
        
        # Sincronizar automaticamente após importação
        auto_sync_to_excel(db)
        
        return {
            "message": "Dados importados com sucesso",
            "loans_imported": result["loans_imported"],
            "history_imported": result["history_imported"]
        }
    except Exception as e:
        # Limpar arquivo temporário em caso de erro
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Erro ao importar do Excel: {str(e)}")


# Mount Frontend at Root (Must be last to avoid shadowing API routes)
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
