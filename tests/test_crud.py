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

def test_select_todos_experimentos(mock_db_connection):
    """
    Testa se a função select_todos_experimentos retorna uma lista de experimentos.
    """
    mock_conn, mock_cursor = mock_db_connection
    # Simula o retorno do banco de dados
    mock_cursor.fetchall.return_value = [
        {'id': 1, 'nome': 'Experimento 1'},
        {'id': 2, 'nome': 'Experimento 2'}
    ]

    # Chama a função
    resultado = crud.select_todos_experimentos(mock_conn)

    # Verifica se a consulta SQL foi executada
    mock_cursor.execute.assert_called_once_with("\n        SELECT * FROM EXPERIMENTO\n    ")
    # Verifica o resultado
    assert "experimentos" in resultado
    assert len(resultado["experimentos"]) == 2
    assert resultado["experimentos"][0]['nome'] == 'Experimento 1'

def test_delete_experimento_sucesso(mock_db_connection):
    """
    Testa a deleção de um experimento com sucesso.
    """
    mock_conn, mock_cursor = mock_db_connection
    # Simula que uma linha foi afetada (deletada)
    mock_cursor.rowcount = 1
    id_experimento = 1

    # Chama a função
    resultado = crud.delete_experimento(mock_conn, id_experimento)

    # Verifica se o comando SQL foi chamado com o ID correto
    mock_cursor.execute.assert_called_once_with("DELETE FROM EXPERIMENTO WHERE id = ?", (id_experimento,))
    # Verifica se o commit foi chamado
    mock_conn.commit.assert_called_once()
    # Verifica se o resultado é o esperado
    assert resultado == 1

def test_delete_experimento_nao_encontrado(mock_db_connection):
    """
    Testa a deleção de um experimento que não existe.
    """
    mock_conn, mock_cursor = mock_db_connection
    # Simula que nenhuma linha foi afetada
    mock_cursor.rowcount = 0
    id_experimento = 999

    # Chama a função
    resultado = crud.delete_experimento(mock_conn, id_experimento)

    # Verifica o resultado
    assert resultado is None

def test_update_experimento_sucesso(mock_db_connection):
    """
    Testa a atualização de um experimento com sucesso.
    """
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 1
    id_experimento = 1
    dados_para_atualizar = [
        "Experimento Atualizado",
        150,
        date(2025, 10, 20),
        6.0,
        600,
        300.0
    ]

    resultado = crud.update_experimento(mock_conn, id_experimento, dados_para_atualizar)

    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
    assert resultado == 1
