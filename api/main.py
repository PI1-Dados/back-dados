from fastapi import FastAPI
import logging
from contextlib import asynccontextmanager
from api.core.database import create_tables, DATABASE_URL
from api.routers import experimentos
from fastapi.middleware.cors import CORSMiddleware

# Configuração de Logging básica
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código a ser executado antes da aplicação iniciar (substitui startup)
    logger.info(f"Conectando ao banco de dados: {DATABASE_URL}")
    create_tables()
    logger.info("Aplicação iniciando... Tabelas do banco de dados verificadas/criadas.")
    yield

    logger.info("Aplicação desligando...")

app = FastAPI(
    title="API de Experimentos Científicos",
    description="API para gerenciar experimentos e seus dados.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(experimentos.router)

@app.get("/", tags=["Root"], summary="Verifica se a API está online")
async def read_root():
    return {"status": "API de Experimentos Online!"}
    
    
