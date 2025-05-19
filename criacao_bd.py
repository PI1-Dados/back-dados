import sqlite3

# Conectar (ou criar) o banco de dados
conexao = sqlite3.connect('experimentos.db')
cursor = conexao.cursor()

# Criar tabela EXPERIMENTOS
cursor.execute('''
CREATE TABLE IF NOT EXISTS EXPERIMENTOS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    nome TEXT NOT NULL
)
''')

# Criar tabela DADOS
cursor.execute('''
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
    fk_exp INTEGER,
    FOREIGN KEY (fk_exp) REFERENCES EXPERIMENTOS(id)
)
''')

# Confirmar e fechar
conexao.commit()
conexao.close()

print("Tabelas criadas com sucesso!")
