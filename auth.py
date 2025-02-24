import jwt
import requests
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer
import os
from dotenv import load_dotenv

# 🔹 Carregar variáveis do .env
load_dotenv()

# 🔹 Configurações do Clerk
CLERK_JWKS_URL = "https://clerk.your-domain.com/.well-known/jwks.json" 
CLERK_AUDIENCE = "your-clerk-audience"  
AUTENTICACAO_ATIVADA = False 

security = HTTPBearer()  # Middleware de autenticação

def get_clerk_public_keys():
    """Obtém as chaves públicas do Clerk para validar JWT."""
    response = requests.get(CLERK_JWKS_URL)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Erro ao obter chaves públicas do Clerk")
    return response.json()

def verify_clerk_token(token: str):
    """Verifica e decodifica o token JWT do Clerk."""
    try:
        header = jwt.get_unverified_header(token)
        jwks = get_clerk_public_keys()
        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)

        if not key:
            raise HTTPException(status_code=403, detail="Chave pública do Clerk não encontrada")

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        decoded_token = jwt.decode(
            token, 
            public_key, 
            algorithms=["RS256"], 
            audience=CLERK_AUDIENCE
        )
        return decoded_token
    except Exception:
        raise HTTPException(status_code=403, detail="Token inválido")

def authenticate_request(auth_header=Depends(security)):
    """Middleware para autenticação dos endpoints protegidos."""
    if not AUTENTICACAO_ATIVADA:
        return None  # 🔹 Se estiver desativado, permite acesso livre

    token = auth_header.credentials
    return verify_clerk_token(token)
