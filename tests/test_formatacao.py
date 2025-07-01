import pytest
from api.utils import formatacao

def test_haversine():
    """
    Testa a função haversine com coordenadas conhecidas.
    A distância entre o centro de São Paulo e o centro do Rio de Janeiro é de aproximadamente 357km.
    """
    lat1, lon1 = -23.550520, -46.633308  # São Paulo
    lat2, lon2 = -22.906847, -43.172897  # Rio de Janeiro
    
    distancia = formatacao.haversine(lat1, lon1, lat2, lon2)
    
    # Verifica se a distância está numa faixa esperada (em metros)
    assert 355000 < distancia < 362000

def test_gerar_csv_dados_vazio():
    """
    Testa a geração de CSV para uma lista de dados vazia.
    """
    assert formatacao.gerar_csv_dados([]) == ""

def test_gerar_csv_dados_com_dados():
    """
    Testa a geração de CSV com dados.
    """
    dados = [
        {'id': 1, 'nome': 'Teste 1'},
        {'id': 2, 'nome': 'Teste 2'}
    ]
    csv_string = formatacao.gerar_csv_dados(dados)
    
    assert "id,nome" in csv_string
    assert "1,Teste 1" in csv_string
    assert "2,Teste 2" in csv_string