# 🚀 Backend - Sistema de Experimentos de Foguetes

Repositório do backend da disciplina de PI1 (2025/1)

## 📋 Pré-requisitos
- **Python 3.10** ou superior
- **Make** (GNU Make)

## ⚡ Como Executar a Aplicação 

1. Caso ainda não haja um ambiente virtual Python, criar um através do comando:
```bash
python3 -m venv .venv
```

2. Certifique-se que está no diretório do projeto e execute o seguinte comando:
```bash
make run
```
> Instala dependências, configura ambiente e inicia o servidor

### Outros comandos úteis

| Comando    | Função                                                                 |
|------------|------------------------------------------------------------------------|
| `make install`  | Cria venv e instala dependências                                       |
| `make setup`    | Configura ambiente (.env + estrutura)                                  |
| `make clean`    | Remove arquivos temporários                                            |

## Acessando a API

Após a inicialização do servidor é disponibilizada uma URL local no terminal que possibilita o acesso a API