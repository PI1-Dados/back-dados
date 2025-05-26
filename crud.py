# crud.py
import sqlite3
from typing import List, Tuple
from datetime import date
import pandas as pd
import io
import logging

# Imports corrigidos para absolutos
import schemas # Assume que schemas.py está no mesmo nível ou PYTHONPATH
from database import get_db_connection # Assume que database.py está no mesmo nível ou PYTHONPATH

logger = logging.getLogger(__name__)

def create_experimento_db(db: sqlite3.Connection, experimento: schemas.ExperimentoCreate, data_obj: date) -> int:
    """
    Insere um novo experimento no banco de dados.
    Retorna o ID do experimento inserido.
    """
    sql = """
        INSERT INTO EXPERIMENTO (nome, distancia_alvo, data, pressao_agua, qtd_litros_agua, peso_foguete)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    cursor = db.cursor()
    try:
        cursor.execute(sql, (
            experimento.nomeExperimento,
            experimento.distanciaAlvo,
            data_obj.isoformat(), # Armazena data como YYYY-MM-DD
            experimento.pressaoAgua,
            experimento.qtdLitrosAgua,
            experimento.pesoFoguete
        ))
        db.commit()
        experimento_id = cursor.lastrowid
        logger.info(f"Experimento '{experimento.nomeExperimento}' inserido com ID: {experimento_id}")
        return experimento_id
    except sqlite3.Error as e:
        db.rollback()
        logger.error(f"Erro ao inserir experimento no DB: {e}")
        raise e # Re-levanta a exceção para ser tratada na rota

def create_dados_experimento_lote_db(db: sqlite3.Connection, dados_lote: List[Tuple]) -> int:
    """
    Insere uma lista de registros de dados de experimento no banco de dados.
    Retorna o número de linhas inseridas.
    """
    if not dados_lote:
        return 0
    
    sql = """
        INSERT INTO DADOS (accel_x, accel_y, accel_z, vel_x, vel_y, vel_z, longitude, latitude, altura, fk_exp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor = db.cursor()
    try:
        cursor.executemany(sql, dados_lote)
        db.commit()
        logger.info(f"{cursor.rowcount} registros inseridos na tabela DADOS.")
        return cursor.rowcount
    except sqlite3.Error as e:
        db.rollback()
        logger.error(f"Erro ao inserir dados do experimento em lote no DB: {e}")
        raise e # Re-levanta a exceção

# Alterado de async def para def
def processar_e_salvar_csv(db: sqlite3.Connection, arquivo_csv_bytes: bytes, experimento_id: int) -> int:
    """
    Lê o conteúdo de um arquivo CSV (em bytes), processa os dados e os salva no banco.
    Retorna o número de registros do CSV processados e salvos.
    Esta função agora é síncrona.
    """
    try:
        arquivo_csv_stream = io.BytesIO(arquivo_csv_bytes)
        # Tenta decodificar como UTF-8, com fallback para latin-1
        try:
            df = pd.read_csv(arquivo_csv_stream, encoding='utf-8', na_filter=True, keep_default_na=True)
        except UnicodeDecodeError:
            df = pd.read_csv(arquivo_csv_stream, encoding='latin-1', na_filter=True, keep_default_na=True)
        
        logger.info(f"CSV lido. Colunas encontradas: {df.columns.tolist()}")

        dados_para_inserir_db = []
        for index, row_data in df.iterrows():
            try:
                schemas.DadosCSV(
                    latitude=row_data.get('latitude'),
                    longitude=row_data.get('longitude'),
                    altitude=row_data.get('altitude')
                )
            except Exception as e_val:
                logger.warning(f"Linha {index} do CSV com dados inválidos: {row_data}. Erro: {e_val}")
                continue

            latitude_csv = row_data.get('latitude')
            longitude_csv = row_data.get('longitude')
            altura_csv = row_data.get('altitude')

            dados_linha_tupla = (
                row_data.get('accel_x'), row_data.get('accel_y'), row_data.get('accel_z'),
                None, None, None,
                longitude_csv,
                latitude_csv,
                altura_csv,
                experimento_id
            )
            dados_para_inserir_db.append(dados_linha_tupla)
        
        if dados_para_inserir_db:
            return create_dados_experimento_lote_db(db, dados_para_inserir_db)
        else:
            logger.info(f"Nenhum dado válido para inserir do CSV para o experimento ID {experimento_id}.")
            return 0

    except pd.errors.EmptyDataError:
        logger.warning("O arquivo CSV está vazio.")
        return 0
    except Exception as e_csv:
        logger.error(f"Erro ao processar o arquivo CSV: {e_csv}")
        raise ValueError(f"Erro ao processar o arquivo CSV: {str(e_csv)}")

