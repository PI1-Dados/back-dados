import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from datetime import date, datetime
import pandas as pd
import io
import logging
import api.schemas.schemas as schemas
from api.utils.formatacao import formata_dados_experimento_especifico


logger = logging.getLogger(__name__)


def create_experimento_db(db: sqlite3.Connection, experimento: schemas.ExperimentoCreate, data_obj: date) -> int:
    """
    Insere um novo experimento no banco de dados.
    """
    sql = """
        INSERT INTO EXPERIMENTO (nome, distancia_alvo, data, pressao_psi, volume_agua, massa_total_foguete)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    cursor = db.cursor()
    try:
        cursor.execute(sql, (
            experimento.nomeExperimento,
            experimento.distanciaAlvo,
            data_obj.isoformat(), # Armazena data como YYYY-MM-DD
            experimento.pressaoBar,
            experimento.volumeAgua,
            experimento.massaTotalFoguete
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
    """
    if not dados_lote:
        return 0
    
    sql = """
        INSERT INTO DADOS_EXPERIMENTO (timestamp, accel_x, accel_y, accel_z, speed_kmph, longitude, latitude, altura, fk_exp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    cursor = db.cursor()
    
    try:
        cursor.executemany(sql, dados_lote)
        db.commit()
        
        logger.info(f"{cursor.rowcount} registros inseridos na tabela DADOS_EXPERIMENTO.")
        
        return cursor.rowcount
    except sqlite3.Error as e:
        db.rollback()
        
        logger.error(f"Erro ao inserir dados do experimento em lote no DB: {e}")
        
        raise e # Re-levanta a exceção

def select_todos_experimentos(db: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    """
    Retorna todos os experimentos, mas apenas seus metadados.
    """
    
    sql = """
        SELECT * FROM EXPERIMENTO
    """
    
    cursor = db.cursor()
    
    cursor.execute(sql)
    dados_rows = cursor.fetchall() # Pega todas as linhas correspondentes
    
    lista_experimentos = [dict(row) for row in dados_rows]
    
    return {
                "experimentos": lista_experimentos,
            }

def select_experimento_completo(db: sqlite3.Connection, id_experimento: int) -> dict:
    """
    Seleciona os detalhes de um experimento e todos os seus registros de dados associados.
    """
    experimento = None

    sql_experimento = """
        SELECT * FROM EXPERIMENTO
        WHERE id = ?
    """
    
    sql_dados_experimento = """
        SELECT timestamp, accel_x, accel_y, accel_z, speed_kmph, longitude, latitude, altura FROM DADOS_EXPERIMENTO
        WHERE fk_exp = ?
        ORDER BY timestamp ASC
    """
    
    cursor = db.cursor()
    
    try:
        # Coleta dados gerais de um único experimento
        cursor.execute(sql_experimento, (id_experimento,))
        experimento = dict(cursor.fetchone())
        
        if not experimento:
            logger.info(f"Experimento com ID {id_experimento} não encontrado.")
            return None

        # Coleta dados de voo do experimento
        cursor.execute(sql_dados_experimento, (id_experimento,))
        dados_experimento = cursor.fetchall()
        
        logger.info(f"Experimento ID {experimento['id']} com {len(dados_experimento)} registros de dados.")
        
        # Monta o resultado final
        resultado_completo = {
            "experimento": experimento,
            "dados_associados": formata_dados_experimento_especifico(dados_experimento)
        }
        
        return resultado_completo
     
    except sqlite3.Error as e:

        logger.error(f"Erro ao selecionar dados para o experimento ID {id_experimento}: {e}")
        raise e # Re-levanta a exceção para ser tratada pelo chamador

def processar_e_salvar_csv(db: sqlite3.Connection, arquivo_csv_bytes: bytes, experimento_id: int) -> int:
    """
    Lê o conteúdo de um arquivo CSV (em bytes), processa os dados e os salva no banco.
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
                    altitude=row_data.get('altitude'),
                    speed_kmph=row_data.get('speed_kmph'),
                    timestamp=row_data.get('timestamp')
                )
            except Exception as e_val:
                logger.warning(f"Linha {index} do CSV com dados inválidos: {row_data}. Erro: {e_val}")
                continue

            dados_linha_tupla = (
                row_data.get('timestamp'),
                row_data.get('accel_x'), row_data.get('accel_y'), row_data.get('accel_z'),
                row_data.get('speed_kmph'),
                row_data.get('latitude'),
                row_data.get('longitude'),
                row_data.get('altitude'),
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

def update_experimento(db: sqlite3.Connection, id_experimento:int, dados_lote: List[Tuple]) -> int:
    """
    Edita os metadados de um experimento no banco de dados.
    """ 

    sql_experimento = """
        UPDATE EXPERIMENTO SET 
        nome = ?, distancia_alvo = ?, data = ?,
        pressao_psi = ?, volume_agua = ?, massa_total_foguete = ?
        WHERE id = ?
    """
    
    if not dados_lote:
        return 0
    
    parametros_finais = dados_lote + [id_experimento]
    
    cursor = db.cursor()
    
    try:
        # Buscar os detalhes do experimento
        cursor.execute(sql_experimento, parametros_finais)

        print(parametros_finais)
        db.commit()

        logger.info(f"Registro do experimento {parametros_finais[-1]} atualizado na tabela EXPERIMENTO!")
        return cursor.rowcount
    
    except sqlite3.Error as e:
        db.rollback()
        logger.error(f"Erro ao atualizar dados do registro de experimento {parametros_finais[-1]} no DB: {e}")
        raise e # Re-levanta a exceção

def delete_experimento(db: sqlite3.Connection, id_experimento: int):
    """
    Deleta um registro da tabela EXPERIMENTO com base no ID fornecido.
    """
    sql = "DELETE FROM EXPERIMENTO WHERE id = ?"
    
    cursor = db.cursor()
    
    try:
        cursor.execute(sql, (id_experimento,))
        db.commit()
        
        # cursor.rowcount informará se alguma linha foi de fato deletada (1) ou não (0)
        if cursor.rowcount > 0:
            logger.info(f"Registro com id {id_experimento} deletado com sucesso da tabela EXPERIMENTO.")
        else:
            logger.warning(f"Nenhum registro encontrado com o id {id_experimento}. Nenhuma linha foi deletada.")
            
        return cursor.rowcount if cursor.rowcount > 0 else None
        
    except sqlite3.Error as e:
        db.rollback()
        logger.error(f"Erro ao deletar o experimento id {id_experimento} no DB: {e}")
        raise e
    finally:
        cursor.close()