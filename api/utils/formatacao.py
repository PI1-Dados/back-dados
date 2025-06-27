import math, io, csv


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

def formata_dados_experimento_especifico(dados_experimento : list):
    dados_registros = []
    distancia_acumulada = 0.0
    altura_inicial = 0.0
    # datetime_inicial = datetime.strptime(dict(dados_experimento[0])['timestamp'], '%Y-%m-%d %H:%M:%S')
    
    for i in range(0, len(dados_experimento)):
        dict_dados = dict(dados_experimento[i])
        
        if i == 0:
            dict_dados['distancia'] = distancia_acumulada
            dict_dados['altura_lancamento'] = altura_inicial
            altura_inicial = dict_dados['altura']
            
        else:
            dict_ant = dict(dados_experimento[i-1])
            
            # tempo_atual_datetime = datetime.strptime(dict_dados['timestamp'], '%Y-%m-%d %H:%M:%S')
            # segundos_atual = (tempo_atual_datetime - datetime_inicial).total_seconds()
            
            distancia_calculada = haversine(dict_ant['latitude'],
                                            dict_ant['longitude'],
                                            dict_dados['latitude'],
                                            dict_dados['longitude'],
                                            )
            
                        
            distancia_acumulada += distancia_calculada
            
            dict_dados['distancia'] = round(distancia_acumulada,2)
            dict_dados['altura_lancamento'] = round(dict_dados['altura'] - altura_inicial,2)
            # dict_dados['timestamp'] = segundos_atual
        
        dados_registros.append(dict_dados)

    
    return dados_registros
    
def gerar_csv_dados(dados : list):
    if not dados:
        return ""

    campos = dados[0].keys()
    buffer = io.StringIO()
    escritor = csv.DictWriter(buffer, fieldnames=campos)
    
    escritor.writeheader()
    escritor.writerows(dados)
    
    return buffer.getvalue()