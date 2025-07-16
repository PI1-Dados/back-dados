import pytest
from api.schemas.schemas import ExperimentoCreate

def test_experimento_create_data_valida():
    """
    Testa se a validação de data aceita o formato correto.
    """
    dados = {
        "nomeExperimento": "Teste Data",
        "distanciaAlvo": 100,
        "dataExperimento": "01/01/2025", # Data válida
        "pressaoBar": 5.0,
        "volumeAgua": 500,
        "massaTotalFoguete": 200
    }
    # Nenhuma exceção deve ser levantada
    experimento = ExperimentoCreate(**dados)
    assert experimento.dataExperimento == "01/01/2025"

def test_experimento_create_data_invalida():
    """
    Testa se a validação de data levanta um erro para o formato incorreto.
    """
    dados = {
        "nomeExperimento": "Teste Data Inválida",
        "distanciaAlvo": 100,
        "dataExperimento": "2025-01-01", # Data inválida
        "pressaoBar": 5.0,
        "volumeAgua": 500,
        "massaTotalFoguete": 200
    }
    with pytest.raises(ValueError, match="Formato de data inválido"):
        ExperimentoCreate(**dados)