from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Database Setup
DATABASE_URL = "sqlite:///./loans.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model - Tabela Emprestimos
class Emprestimo(Base):
    __tablename__ = "emprestimos"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, index=True)
    instituicao_credora = Column(String)
    valor_parcela = Column(Float)
    qtd_total_parcelas = Column(Integer)
    qtd_parcelas_devidas = Column(Integer)
    valor_parcela_adiantada = Column(Float)
    taxa_selic_registro = Column(Float)
    taxa_cdi_registro = Column(Float)
    data_cadastro = Column(String)  # ISO format YYYY-MM-DD
    dia_vencimento = Column(Integer)
    
    # Relationship to historical values
    historicos = relationship("HistoricoValorAdiantado", back_populates="emprestimo", cascade="all, delete-orphan")


# Database Model - Tabela Histórico de Valores Adiantados
class HistoricoValorAdiantado(Base):
    __tablename__ = "historico_valores_adiantados"
    
    id = Column(Integer, primary_key=True, index=True)
    emprestimo_id = Column(Integer, ForeignKey("emprestimos.id"), nullable=False)
    data_registro = Column(String, nullable=False)  # ISO format YYYY-MM-DD
    valor_parcela_adiantada = Column(Float, nullable=False)
    taxa_selic = Column(Float)
    taxa_cdi = Column(Float)
    
    # Relationship back to loan
    emprestimo = relationship("Emprestimo", back_populates="historicos")


def init_db():
    Base.metadata.create_all(bind=engine)
