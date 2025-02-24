import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Pegando a URL do banco de dados do .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Criando a conexão com o PostgreSQL
def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)
