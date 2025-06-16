import sqlite3
import logging, os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_SQLITE')

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    if DATABASE_URL:
        logger.info(f"Conectando ao banco de dados: {DATABASE_URL}")
        conn = sqlite3.connect(DATABASE_URL) 

        # conn.close()
    else:
        logger.error("A variável de ambiente DATABASE_SQLITE não foi definida.")

        raise ValueError("Configuração crítica ausente: DATABASE_SQLITE não foi definida no ambiente ou arquivo .env.")

    
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return conn

def create_tables():
    """Cria as tabelas no banco de dados se não existirem."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Tabela EXPERIMENTO
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS EXPERIMENTO (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(80) NOT NULL,
            distancia_alvo INT NOT NULL,
            data DATE NOT NULL,
            pressao_psi FLOAT NOT NULL,
            volume_agua FLOAT NOT NULL,
            massa_total_foguete FLOAT NOT NULL
        )
        """)
        logger.info("Tabela EXPERIMENTO verificada/criada.")

        # Tabela DADOS_EXPERIMENTO
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS DADOS_EXPERIMENTO (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            accel_x REAL,
            accel_y REAL,
            accel_z REAL,
            speed_kmph REAL,
            longitude REAL,
            latitude REAL,
            altura REAL,
            fk_exp INTEGER NOT NULL,
            FOREIGN KEY (fk_exp) REFERENCES EXPERIMENTO(id) ON DELETE CASCADE
        )
        """)
        logger.info("Tabela DADOS_EXPERIMENTO verificada/criada.")
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        conn.rollback()
    finally:
        conn.close()
