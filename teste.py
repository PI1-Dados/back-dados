import sqlite3
import math, os
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from database import DATABASE_URL
import dotenv

dotenv.load_dotenv()


def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula a distância em metros entre dois pontos geográficos (latitude, longitude)
    usando a fórmula de Haversine.
    """
    R = 6371000  # Raio da Terra em metros

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def get_dados_experimento(experimento_id: int):
    """
    Busca latitude, longitude e timestamp para um dado experimento_id,
    ordenados por timestamp.
    """
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT timestamp, latitude, longitude, speed_kmph
        FROM DADOS_EXPERIMENTO 
        WHERE fk_exp = ? AND latitude IS NOT NULL AND longitude IS NOT NULL AND timestamp IS NOT NULL
        ORDER BY timestamp ASC 
    """, (experimento_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return rows

def plot_distancia_acumulada_vs_tempo(experimento_id: int, nome_experimento: str = "Experimento"):
    """
    Gera e salva um gráfico de distância acumulada vs. tempo para o experimento.
    """
    dados = get_dados_experimento(experimento_id)

    if not dados or len(dados) < 2:
        print(f"Não há dados suficientes para gerar o gráfico para o experimento ID {experimento_id}.")
        return

    tempos = []
    distancias_acumuladas = []
    distancia_total = 0.0
    
    # Parse do primeiro timestamp para referência de tempo decorrido
    try:
        primeiro_timestamp_obj = datetime.strptime(dados[0]['timestamp'], '%Y-%m-%d %H:%M:%S')

    except ValueError as e:
        print(f"Erro ao parsear o primeiro timestamp: {dados[0]['timestamp']}. Erro: {e}")

        try:
            primeiro_timestamp_obj = datetime.fromisoformat(dados[0]['timestamp'])
        except ValueError:
            print("Não foi possível parsear o timestamp. Verifique o formato no CSV e no banco.")
            return


    ponto_anterior = {
        'lat': dados[0]['latitude'],
        'lon': dados[0]['longitude'],
        'time_obj': primeiro_timestamp_obj
    }

    tempos.append(primeiro_timestamp_obj) # Usar objetos datetime para o eixo x
    distancias_acumuladas.append(0.0)

    for i in range(1, len(dados)):
        linha_atual = dados[i]
        
        try:
            timestamp_atual_obj = datetime.strptime(linha_atual['timestamp'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                timestamp_atual_obj = datetime.fromisoformat(linha_atual['timestamp'])
            except ValueError:
                print(f"Pulando linha devido a erro no parse do timestamp: {linha_atual['timestamp']}")
                continue


        lat_atual = linha_atual['latitude']
        lon_atual = linha_atual['longitude']

        distancia_segmento = haversine(ponto_anterior['lat'], ponto_anterior['lon'], lat_atual, lon_atual)
        distancia_total += distancia_segmento

        tempos.append(timestamp_atual_obj)
        distancias_acumuladas.append(distancia_total / 1000)  # Convertendo para km

        ponto_anterior['lat'] = lat_atual
        ponto_anterior['lon'] = lon_atual
        ponto_anterior['time_obj'] = timestamp_atual_obj

    # Plotagem
    plt.figure(figsize=(12, 6))
    plt.plot(tempos, distancias_acumuladas, marker='o', linestyle='-')
    
    plt.xlabel("Tempo")
    plt.ylabel("Distância Acumulada (m)")
    plt.title(f"Distância Acumulada vs. Tempo - {nome_experimento} (ID: {experimento_id})")
    plt.grid(True)
    
    # Formatar o eixo x para mostrar datas/horas de forma legível
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10)) # Ajusta o número de ticks
    plt.gcf().autofmt_xdate() # Rotaciona as datas para melhor visualização

    # Salvar o gráfico
    nome_arquivo_grafico = f"distancia_vs_tempo_exp_{experimento_id}.png"
    plt.savefig(nome_arquivo_grafico)
    print(f"Gráfico salvo como '{nome_arquivo_grafico}'")
    plt.show()

# --- GRÁFICO DE VELOCIDADE VS. TEMPO ---
def plot_velocidade_vs_tempo(experimento_id: int, nome_experimento: str="Experimento vel"):
    """
    Gera o gráfico de Velocidade (km/h) vs. Tempo.
    """
    
    dados = get_dados_experimento(experimento_id)

    if not dados or len(dados) < 2:
        print(f"Não há dados suficientes para gerar o gráfico para o experimento ID {experimento_id}.")
        return

    tempos = [datetime.strptime(d['timestamp'], '%Y-%m-%d %H:%M:%S') for d in dados]
    velocidades = [d['speed_kpmh'] for d in dados]

    plt.figure(figsize=(12, 6))
    plt.plot(tempos, velocidades, color='blue', linestyle='-')
    
    plt.xlabel("Tempo")
    plt.ylabel("Velocidade (km/h)")
    plt.title(f"Velocidade vs. Tempo - {nome_experimento}")
    plt.grid(True)
    
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gcf().autofmt_xdate()

    nome_arquivo = f"velocidade_vs_tempo_exp_{experimento_id}.png"
    plt.savefig(nome_arquivo)
    print(f"Gráfico de velocidade salvo como '{nome_arquivo}'")

# --- GRÁFICO DE ACELERAÇÃO VS. TEMPO ---
def plot_aceleracao_vs_tempo(experimento_id: int, dados, nome_experimento: str):
    """
    Calcula a aceleração a partir da velocidade e gera o gráfico de Aceleração (m/s²) vs. Tempo.
    """
    if len(dados) < 2:
        print("Dados insuficientes para calcular aceleração.")
        return

    tempos_aceleracao = []
    aceleracoes = []

    for i in range(1, len(dados)):
        ponto_anterior = dados[i-1]
        ponto_atual = dados[i]

        # Converter velocidades de km/h para m/s
        v_anterior_ms = ponto_anterior['speed_kpmh'] * (1000 / 3600)
        v_atual_ms = ponto_atual['speed_kpmh'] * (1000 / 3600)

        # Converter timestamps para objetos datetime e calcular delta T em segundos
        t_anterior = datetime.strptime(ponto_anterior['timestamp'], '%Y-%m-%d %H:%M:%S')
        t_atual = datetime.strptime(ponto_atual['timestamp'], '%Y-%m-%d %H:%M:%S')
        delta_t_s = (t_atual - t_anterior).total_seconds()

        if delta_t_s > 0:
            # Calcular aceleração: a = (v_final - v_inicial) / delta_t
            aceleracao = (v_atual_ms - v_anterior_ms) / delta_t_s
            aceleracoes.append(aceleracao)
            tempos_aceleracao.append(t_atual) # Associar aceleração com o timestamp do ponto final do intervalo

    if not tempos_aceleracao:
        print("Não foi possível calcular nenhum ponto de aceleração.")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(tempos_aceleracao, aceleracoes, color='red', linestyle='-')
    
    plt.xlabel("Tempo")
    plt.ylabel("Aceleração (m/s²)")
    plt.title(f"Aceleração vs. Tempo - {nome_experimento}")
    plt.grid(True)
    
    # Linha horizontal em 0 para referência
    plt.axhline(0, color='black', linewidth=0.8, linestyle='--')

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gcf().autofmt_xdate()

    nome_arquivo = f"aceleracao_vs_tempo_exp_{experimento_id}.png"
    plt.savefig(nome_arquivo)
    print(f"Gráfico de aceleração salvo como '{nome_arquivo}'")

# if __name__ == "__main__":
#     # Exemplo de como usar:
#     # Primeiro, certifique-se de que a tabela EXPERIMENTO tem algum ID.
#     # Você pode descobrir um ID de experimento válido consultando seu DB.
#     id_do_experimento_para_plotar = 1 # Substitua pelo ID do experimento desejado
    
#     # Opcional: buscar nome do experimento para o título do gráfico
#     # conn_main = sqlite3.connect(DATABASE_URL)
#     # cursor_main = conn_main.cursor()
#     # cursor_main.execute("SELECT nome FROM EXPERIMENTO WHERE id = ?", (id_do_experimento_para_plotar,))
#     # res = cursor_main.fetchone()
#     # nome_exp = f"Experimento {id_do_experimento_para_plotar}" if not res else res[0]
#     # conn_main.close()

#     # plot_distancia_acumulada_vs_tempo(id_do_experimento_para_plotar, nome_exp)
#     plot_distancia_acumulada_vs_tempo(id_do_experimento_para_plotar, f"Experimento {id_do_experimento_para_plotar}")

