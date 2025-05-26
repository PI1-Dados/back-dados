# main.py
from fastapi import FastAPI
import logging
from contextlib import asynccontextmanager

# Importa funções e routers dos outros módulos
from database import create_tables, DATABASE_URL # Ajuste se necessário
from routers import experimentos # Importa o módulo do router

# Configuração de Logging básica
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gerenciador de contexto Lifespan para eventos de inicialização e desligamento
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código a ser executado antes da aplicação iniciar (substitui startup)
    logger.info(f"Conectando ao banco de dados: {DATABASE_URL}")
    create_tables()
    logger.info("Aplicação iniciando... Tabelas do banco de dados verificadas/criadas.")
    yield
    # Código a ser executado após a aplicação desligar (substitui shutdown)
    logger.info("Aplicação desligando...")

app = FastAPI(
    title="API de Experimentos Científicos",
    description="API para gerenciar experimentos e seus dados.",
    version="1.0.0",
    lifespan=lifespan # Adiciona o gerenciador de lifespan
)

# Inclui o router de experimentos na aplicação principal
app.include_router(experimentos.router)

@app.get("/", tags=["Root"], summary="Verifica se a API está online")
async def read_root():
    return {"status": "API de Experimentos Online!"}

# Para executar (no terminal, no diretório raiz do projeto):
# uvicorn main:app --reload
