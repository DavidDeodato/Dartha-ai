import os
import importlib
#importando o env
from dotenv import load_dotenv


# Carregar variáveis do .env
load_dotenv()

def get_model_class(module_name, class_name):
    """Carrega a classe do modelo dinamicamente."""
    module = importlib.import_module(f"models.{module_name}")
    return getattr(module, class_name)

SEGMENT_CONFIG = {
    "X5": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "db_url": os.getenv("DATABASE_URL"),
        "models": {
            "GIX5": lambda api_key: get_model_class("gix5", "GIX5Agent")(api_key),
            "LEGAL": lambda api_key: get_model_class("legal", "LegalAI")(api_key),
            "BNCC": lambda api_key: get_model_class("bncc", "BNCCAgent")(api_key),
            "PEE": lambda api_key: get_model_class("pee", "PEEAgent")(api_key),
        }
    },
    "ESCOLAS": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "db_url": os.getenv("DATABASE_URL"),  # 🔥 Verifique se isso não está retornando None
        "models": {
            "BNCC": lambda api_key: get_model_class("bncc", "BNCCAgent")(api_key),
        }
    }
}

# 🔍 Debug: Verifique se a URL do banco está correta
for segment, config in SEGMENT_CONFIG.items():
    print(f"🔎 Segmento: {segment}, DB_URL: {config['db_url']}")
