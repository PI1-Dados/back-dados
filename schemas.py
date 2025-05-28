# schemas.py
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

class ExperimentoBase(BaseModel):
    nomeExperimento: str
    distanciaAlvo: int
    dataExperimento: str  # Formato dd/mm/yyyy
    pressaoAgua: float
    qtdLitrosAgua: float
    pesoFoguete: float

    @field_validator('dataExperimento')
    @classmethod
    def valida_formato_data(cls, v_data: str) -> str:
        try:
            datetime.strptime(v_data, "%d/%m/%Y").date()
            return v_data
        except ValueError:
            raise ValueError("Formato de data inválido para 'dataExperimento'. Use dd/mm/yyyy.")

class ExperimentoCreate(ExperimentoBase):
    pass

class Experimento(ExperimentoBase):
    id: int
    model_config = ConfigDict(from_attributes=True) # Substitui orm_mode = True


class DadosExperimentoBase(BaseModel):
    accel_x: Optional[float] = None
    accel_y: Optional[float] = None
    accel_z: Optional[float] = None
    speed_kmph: Optional[float] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    height: Optional[float] = None
    fk_exp: int

class DadosExperimentoCreate(DadosExperimentoBase):
    pass

class DadosExperimento(DadosExperimentoBase):
    id: int
    model_config = ConfigDict(from_attributes=True) # Substitui orm_mode = True

# Modelo para os dados que vêm do CSV (apenas os campos que serão usados)
class DadosCSV(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    # Outros campos do CSV podem ser adicionados aqui se necessário para validação
    timestamp: Optional[str] = None
    speed_kmph: Optional[float] = None
    # satellites: Optional[int] = None
    # hdop: Optional[float] = None
