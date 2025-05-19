from fastapi import FastAPI, HTTPException
import sqlite3
from typing import List
from pydantic import BaseModel

app = FastAPI()

DATABASE = "experimentos.db"

# --- MODELOS DE RESPOSTA ---

class Experimento(BaseModel):
    id: int
    data: str
    nome: str

class Dado(BaseModel):
    id: int
    accel_x: float
    accel_y: float
    accel_z: float
    vel_x: float
    vel_y: float
    vel_z: float
    longitude: float
    latitude: float
    altura: float
    fk_exp: int

# --- ROTAS ---

@app.get("/experimentos", response_model=List[Experimento])
def get_experimentos():
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM EXPERIMENTOS")
    rows = cur.fetchall()
    con.close()
    return [dict(row) for row in rows]

@app.get("/dados/{fk_exp}", response_model=List[Dado])
def get_dados_por_experimento(fk_exp: int):
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM DADOS WHERE fk_exp = ?", (fk_exp,))
    rows = cur.fetchall()
    con.close()
    if not rows:
        raise HTTPException(status_code=404, detail="Nenhum dado encontrado para esse experimento.")
    return [dict(row) for row in rows]
