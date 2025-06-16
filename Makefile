.PHONY: run install setup clean check-env

# Variáveis
VENV = .venv
DB_DIR = db
DB_FILE = $(DB_DIR)/experimentos.db
ENV_FILE = .env

# Detecção de SO
ifeq ($(OS),Windows_NT)
    # Windows
    PYTHON = python
    PIP = $(VENV)/Scripts/pip
    UVICORN = $(VENV)/Scripts/uvicorn
    RM = cmd /C "rmdir /S /Q"
    MKDIR = cmd /C "mkdir"
    COPY = cmd /C "copy"
    DB_CHECK = if not exist "$(DB_FILE)" type nul > "$(DB_FILE)"
else
    # Linux/macOS
    PYTHON = python3
    PIP = $(VENV)/bin/pip
    UVICORN = $(VENV)/bin/uvicorn
    RM = rm -rf
    MKDIR = mkdir -p
    COPY = cp
    DB_CHECK = touch "$(DB_FILE)"
endif

# Alvo principal
run: check-env install setup
	@echo "\n🚀 Iniciando servidor..."
	$(UVICORN) main:app --reload

# Verifica Python
check-env:
	@$(PYTHON) -c "import sys; assert sys.version_info >= (3, 10), 'Use Python 3.10+'"

# Instala dependências
install: $(VENV)/bin/activate
	@echo "\n📦 Instalando dependências..."
	$(PIP) install -r requirements.txt

# Configura ambiente
setup: $(ENV_FILE) $(DB_DIR)
	@if [ ! -f "$(DB_FILE)" ]; then \
		echo "Criando banco de dados em $(DB_FILE)"; \
		$(DB_CHECK); \
	fi

# Ambiente virtual
$(VENV)/bin/activate:
	@echo "\n🐍 Criando ambiente virtual..."
	$(PYTHON) -m venv $(VENV)

# Diretório db
$(DB_DIR):
	$(MKDIR) $(DB_DIR)

# Arquivo .env
$(ENV_FILE):
	@echo "\n🔧 Criando .env..."
	$(COPY) .env.exemplo $(ENV_FILE)
	@echo "Configure as variáveis em $(ENV_FILE)"

# Limpeza
clean:
	@echo "\n🧹 Limpando ambiente..."
	$(RM) $(VENV)
	$(RM) __pycache__
	$(RM) */__pycache__

help:
	@echo "Comandos disponíveis:"
	@echo "  make run     - Inicia o servidor"
	@echo "  make install - Instala dependências"
	@echo "  make setup   - Configura ambiente"
	@echo "  make clean   - Limpa o ambiente"