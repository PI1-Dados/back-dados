from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool # Importado para rodar código síncrono em thread separada
from typing import Annotated
from datetime import datetime

from fastapi.responses import StreamingResponse
from api.utils.formatacao import gerar_csv_dados
from api.utils.graficos_teste import plot_distancia_acumulada_vs_tempo
import sqlite3
import logging, traceback
import api.utils.crud as crud
import api.schemas.schemas as schemas
from api.core.database import get_db_connection


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/experimentos",
    tags=["Experimentos"]
)

def get_db():
    db = get_db_connection()
    try:
        yield db
    finally:
        db.close()

DbDependency = Annotated[sqlite3.Connection, Depends(get_db)]

@router.get("")
async def busca_todos_experimentos(db:DbDependency):
    exp = await run_in_threadpool(crud.select_todos_experimentos, db)
    
    return exp

@router.get("/{id_experimento}")
async def busca_experimento(db:DbDependency, id_experimento):
    exp = await run_in_threadpool(crud.select_experimento_completo, db, id_experimento)
    
    return exp

@router.post("/novo", summary="Cria um novo experimento com dados de um CSV")
async def criar_novo_experimento_rota(
    db: DbDependency,
    nomeExperimento: str = Form(..., description="Nome do experimento"),
    distanciaAlvo: int = Form(..., description="Distância alvo em metros"),
    dataExperimento: str = Form(..., description="Data do experimento no formato dd/mm/yyyy"),
    pressaoBar: float = Form(..., description="Pressão da água em BAR"),
    volumeAgua: float = Form(..., description="Quantidade de ml de água"),
    massaTotalFoguete: float = Form(..., description="Peso do foguete em gramas"),
    arquivoDados: UploadFile = File(..., description="Arquivo CSV com os dados do lançamento/experimento")
):

    # Verificação para formatação de data e formato do arquivo enviado
    try:
        data_experimento_obj = datetime.strptime(dataExperimento, "%d/%m/%Y").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato de data inválido para 'dataExperimento'. Use dd/mm/yyyy."
        )

    if not arquivoDados.filename.endswith(('.csv', '.CSV')):
        raise HTTPException(
            status_code=400,
            detail="Tipo de arquivo inválido para 'arquivoDados'. Envie um arquivo CSV."
        )
    
    if arquivoDados.content_type not in ["text/csv", "application/vnd.ms-excel", "text/plain", "application/octet-stream"]:
        logger.warning(f"Content-Type do arquivo: {arquivoDados.content_type}. Verifique se é realmente um CSV.")

    experimento_schema = schemas.ExperimentoCreate(
        nomeExperimento=nomeExperimento,
        distanciaAlvo=distanciaAlvo,
        dataExperimento=dataExperimento,
        pressaoBar=pressaoBar,
        volumeAgua=volumeAgua,
        massaTotalFoguete=massaTotalFoguete
    )
    
    experimento_id = None
    registros_csv_salvos = 0

    try:
        experimento_id = await run_in_threadpool(
            crud.create_experimento_db, db, experimento_schema, data_experimento_obj
        )
        
        conteudo_csv_bytes = await arquivoDados.read() # Leitura do arquivo é assíncrona
        
        if conteudo_csv_bytes: # Verifica se o arquivo tem conteúdo
            registros_csv_salvos = await run_in_threadpool(
                crud.processar_e_salvar_csv, db, conteudo_csv_bytes, experimento_id
            )
        else:
            logger.info(f"Arquivo CSV '{arquivoDados.filename}' está vazio, nenhum dado de CSV para processar.")


    except sqlite3.Error as e_db:
        logger.error(f"Erro de banco de dados na rota: {e_db}")

        raise HTTPException(status_code=500, detail=f"Erro de banco de dados: {str(e_db)}")
  
    except ValueError as e_val: 
        logger.error(f"Erro de validação/processamento de dados: {e_val}")

        if experimento_id:
             logger.warning(f"Experimento ID {experimento_id} foi criado, mas houve erro ao processar CSV: {e_val}")

        raise HTTPException(status_code=400, detail=str(e_val))

    except Exception as e_geral:
        logger.error(f"Erro geral inesperado na rota: {e_geral}")
        
        raise HTTPException(status_code=500, detail=f"Erro inesperado no servidor: {str(e_geral)}")

    return {
        "mensagem": "Experimento e dados do CSV processados e salvos com sucesso!",
        "experimento_id": experimento_id,
        "nome_experimento": nomeExperimento,
        "data_experimento": data_experimento_obj.isoformat(),
        "nome_arquivo_csv": arquivoDados.filename,
        "registros_csv_processados": registros_csv_salvos
    }

@router.put("/{id_experimento}", summary="Atualiza (substitui) um experimento")
async def atualizar_experimento_completo_rota(
    id_experimento: int,
    db: DbDependency,
    nomeExperimento: str = Form(..., description="Nome do experimento"),
    distanciaAlvo: int = Form(..., description="Distância alvo em metros"),
    dataExperimento: str = Form(..., description="Data do experimento no formato dd/mm/yyyy"),
    pressaoBar: float = Form(..., description="Pressão da água em BAR"),
    volumeAgua: float = Form(..., description="Quantidade de ml de água"),
    massaTotalFoguete: float = Form(..., description="Peso do foguete em gramas")
):
    experimento_existente = await run_in_threadpool(crud.select_experimento_completo, db, id_experimento)
    if not experimento_existente:
        raise HTTPException(status_code=404, detail=f"Experimento com id {id_experimento} não encontrado.")

    # Bloco principal try/except para erros de banco de dados ou inesperados
    try:
        try:
            data_obj = datetime.strptime(dataExperimento, "%d/%m/%Y").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de data inválido para 'dataExperimento'. Use dd/mm/yyyy."
            )

        dados_experimento_schema = schemas.ExperimentoCreate(
            nomeExperimento=nomeExperimento,
            distanciaAlvo=distanciaAlvo,
            dataExperimento=dataExperimento, # Mantém como string para o schema
            pressaoBar=pressaoBar,
            volumeAgua=volumeAgua,
            massaTotalFoguete=massaTotalFoguete
        )

        dados_para_db = [
            dados_experimento_schema.nomeExperimento,
            dados_experimento_schema.distanciaAlvo,
            data_obj,  # Usa o objeto de data já convertido
            dados_experimento_schema.pressaoBar,
            dados_experimento_schema.volumeAgua,
            dados_experimento_schema.massaTotalFoguete,
        ]

        await run_in_threadpool(crud.update_experimento, db, id_experimento, dados_para_db)

    except sqlite3.Error as e_db:
        logger.error(f"Erro de banco de dados na rota PUT: {e_db}")
        
        raise HTTPException(status_code=500, detail=f"Erro de banco de dados: {str(e_db)}")
    
    except Exception as e_geral:
        logger.error(f"Erro geral inesperado na rota PUT: {e_geral}")
       
        raise HTTPException(status_code=500, detail=f"Erro inesperado no servidor: {str(e_geral)}")

    return {
        "mensagem": f"Experimento com ID {id_experimento} atualizado com sucesso!"
        }
    
@router.delete("/{id_experimento}")
async def deleta_experimento(db:DbDependency, id_experimento):
    exp = await run_in_threadpool(crud.delete_experimento, db, id_experimento)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experimento com {id_experimento} não encontrado")
    
    return {
        "mensagem": f"Experimento com ID {id_experimento} deletado com sucesso!"
        }

@router.get("/download-csv/{id_experimento}")
async def faz_download_csv_experimento(db: DbDependency, id_experimento):
    try:
        exp = await run_in_threadpool(crud.select_experimento_completo, db, id_experimento)

        if not exp:
            raise HTTPException(status_code=404, detail="Item não encontrado apra gerar CSV")

        saida_csv = gerar_csv_dados(exp['dados_associados'])
        
        return StreamingResponse(
            saida_csv,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={exp['experimento']['nome']}.csv"
            }
        )    
        
    except Exception as e:
        print(traceback.print_exc())
        
        return {
            "mensagem": f"Erro na geração do CSV!",
            "erro" : traceback.print_exc()
        }
    

@router.get("/gerar-grafico/{id_experimento}")
async def mostra_grafico(id_experimento):
    plot_distancia_acumulada_vs_tempo(id_experimento)