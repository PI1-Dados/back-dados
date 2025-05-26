# back-dados
Repositório do backend do software da matéria de PI1 2025/1

# Como executar a aplicação (Linux)

0. Certifique-se de ter o python 3.10.X instalado

1. Crie um ambiente virtual Python através do comando `python3 -m venv .venv`

2. Entre no ambiente recém-criado pelo comando `source .venv/bin/activate`

3. Instale as dependências utilizadas pelo projeto pelo comando `pip install -r requirements.txt`

4. Inicie a aplicação levantando um servidor local pelo uvicorn com o comando `uvicorn main:app --reload`
