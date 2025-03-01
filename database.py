import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from config import SEGMENT_CONFIG # - para saber quais segmentos estão disponíveis e ai poder pegar o certo

# Carregar variáveis do .env
load_dotenv()

def get_connection(segment):
    """Retorna a conexão com o banco de dados correto baseado no segmento."""
    segment_data = SEGMENT_CONFIG.get(segment)
    
    if not segment_data:
        raise ValueError(f"Segmento inválido: {segment}")

    db_url = segment_data["db_url"]  # Agora acessamos corretamente
    if not db_url:
        raise ValueError(f"DB_URL não configurado para o segmento: {segment}")

    return psycopg.connect(db_url, row_factory=dict_row)

