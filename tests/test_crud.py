import pytest
from unittest.mock import MagicMock, ANY
from datetime import date
import sqlite3

# Módulos da sua aplicação que serão testados
from api.utils import crud
from api.schemas import schemas

# Fixture do Pytest para simular a conexão com o banco de dados
@pytest.fixture
def mock_db_connection(mocker):
    """Cria um mock da conexão com o banco de dados e seu cursor."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    mock_cursor = MagicMock()
    
    # Configura o mock da conexão para retornar o mock do cursor
    mock_conn.cursor.return_value = mock_cursor
    
    # Configura o mock do cursor para simular o lastrowid
    mock_cursor.lastrowid = 1
    
    return mock_conn, mock_cursor

# Fixture para os dados de um experimento
@pytest.fixture
def experimento_data():
    """Retorna um objeto de schema para ser usado nos testes."""
    return schemas.ExperimentoCreate(
        nomeExperimento="Teste de Lançamento",
        distanciaAlvo=100,
        dataExperimento="25/12/2025",
        pressaoBar=5.5,
        volumeAgua=500,
        massaTotalFoguete=250.5
    )

def test_create_experimento_db_sucesso(mock_db_connection, experimento_data):
    """
    Testa a função create_experimento_db em um cenário de sucesso.
    """
    mock_conn, mock_cursor = mock_db_connection
    data_obj = date(2025, 12, 25)

    # Chama a função que está sendo testada
    experimento_id = crud.create_experimento_db(mock_conn, experimento_data, data_obj)

    # Verifica se o cursor.execute foi chamado com o SQL e os parâmetros corretos
    mock_cursor.execute.assert_called_once_with(
        # A quebra de linha e espaços no SQL devem corresponder exatamente ao da função original
        "\n        INSERT INTO EXPERIMENTO (nome, distancia_alvo, data, pressao_psi, volume_agua, massa_total_foguete)\n        VALUES (?, ?, ?, ?, ?, ?)\n    ",
        (
            experimento_data.nomeExperimento,
            experimento_data.distanciaAlvo,
            data_obj.isoformat(),
            experimento_data.pressaoBar,
            experimento_data.volumeAgua,
            experimento_data.massaTotalFoguete
        )
    )

    # Verifica se o commit foi chamado
    mock_conn.commit.assert_called_once()

    # Verifica se o rollback NÃO foi chamado
    mock_conn.rollback.assert_not_called()
    
    # Verifica se o ID retornado é o esperado (configurado no mock)
    assert experimento_id == 1

def test_create_experimento_db_falha_sqlite(mock_db_connection, experimento_data):
    """
    Testa a função create_experimento_db quando o banco de dados lança uma exceção.
    """
    mock_conn, mock_cursor = mock_db_connection
    data_obj = date(2025, 12, 25)

    # Configura o mock para simular um erro do SQLite ao executar
    mock_cursor.execute.side_effect = sqlite3.Error("Erro simulado no banco de dados")

    # Verifica se a exceção do SQLite é propagada corretamente
    with pytest.raises(sqlite3.Error):
        crud.create_experimento_db(mock_conn, experimento_data, data_obj)

    # Verifica se o execute foi chamado
    mock_cursor.execute.assert_called_once()

    # Verifica se o rollback foi chamado em caso de erro
    mock_conn.rollback.assert_called_once()

    # Verifica se o commit NÃO foi chamado
    mock_conn.commit.assert_not_called()