# database.py
import sqlite3
import logging, os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_SQLITE')

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    if DATABASE_URL:
        # Dentro deste bloco, o verificador de tipos sabe que DATABASE_URL é uma str,
        # porque a condição DATABASE_URL (que avalia para True se não for None ou string vazia) passou.
        logger.info(f"Conectando ao banco de dados: {DATABASE_URL}")
        conn = sqlite3.connect(DATABASE_URL) # ✅ Seguro para chamar aqui
        # ... seu código para usar a conexão ...
        # conn.close() # Lembre-se de fechar a conexão
    else:
        logger.error("A variável de ambiente DATABASE_SQLITE não foi definida.")
        # É uma boa prática tratar esse caso explicitamente:
        # Opção 1: Levantar um erro e parar a execução
        raise ValueError("Configuração crítica ausente: DATABASE_SQLITE não foi definida no ambiente ou arquivo .env.")
        # Opção 2: Usar um valor padrão (se fizer sentido para sua aplicação)
        # logger.warning("DATABASE_SQLITE não definida, usando banco de dados em memória ou padrão.")
        # conn = sqlite3.connect(':memory:') # Exemplo de fallback
        # Opção 3: Sair da aplicação
        # import sys
        # sys.exit("Erro: DATABASE_SQLITE não configurada.")
    
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
            pressao_agua FLOAT NOT NULL,
            qtd_litros_agua FLOAT NOT NULL,
            peso_foguete FLOAT NOT NULL
        )
        """)
        logger.info("Tabela EXPERIMENTO verificada/criada.")

        # Tabela DADOS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS DADOS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            accel_x REAL,
            accel_y REAL,
            accel_z REAL,
            vel_x REAL,
            vel_y REAL,
            vel_z REAL,
            longitude REAL,
            latitude REAL,
            altura REAL,
            fk_exp INTEGER NOT NULL,
            FOREIGN KEY (fk_exp) REFERENCES EXPERIMENTO(id) ON DELETE CASCADE
        )
        """)
        logger.info("Tabela DADOS verificada/criada.")
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        conn.rollback()
    finally:
        conn.close()
