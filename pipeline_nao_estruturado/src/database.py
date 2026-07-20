import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# 1. Força o Python a ler o arquivo .env que está na raiz do projeto
load_dotenv()

# 2. Captura a URL real. Sem hardcode (chumbamento) de senhas no código.
DATABASE_URL = os.getenv("DATABASE_URL")

# Trava de segurança
if not DATABASE_URL:
    raise ValueError("ERRO: A variável DATABASE_URL não foi encontrada. Verifique se o arquivo .env foi criado na raiz do projeto (fora da pasta src) e se o nome está correto.")

# 3. Inicializa o motor de conexão
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==================== MODELAGEM DAS TABELAS ====================
class BronzeDocumentos(Base):
    """Camada Bronze: Catálogo com validação de integridade por Hash SHA-256."""
    __tablename__ = "bronze_documentos"

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String, nullable=False)
    hash_documento = Column(String, unique=True, index=True, nullable=False)
    url_origem = Column(String, nullable=True)
    data_processamento = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Processado")

    dados_extraidos = relationship("PrataExtracao", back_populates="documento")


class PrataExtracao(Base):
    """Camada Prata: Dados limpos indexados para queries diretas no banco."""
    __tablename__ = "prata_extracao"

    id = Column(Integer, primary_key=True, index=True)
    documento_id = Column(Integer, ForeignKey("bronze_documentos.id"), nullable=False)
    dados_json = Column(JSONB, nullable=False) 

    documento = relationship("BronzeDocumentos", back_populates="dados_extraidos")

# ==================== EXECUÇÃO ====================
def criar_tabelas():
    Base.metadata.create_all(bind=engine)
    print("Tabelas verificadas/criadas com sucesso no PostgreSQL em nuvem.")

if __name__ == "__main__":
    criar_tabelas()