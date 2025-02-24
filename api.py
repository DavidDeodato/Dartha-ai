from fastapi import FastAPI, Depends
from pydantic import BaseModel
from database import get_connection
from db_queries import create_chat, save_message, get_chat_history
from models.gix5 import GIX5Agent
from auth import authenticate_request  # 🔒 Middleware de autenticação
import time

# Variável para ativar/desativar
AUTENTICACAO_ATIVADA = True

app = FastAPI()

# Dicionário de agentes
agents = {
    "GIX5": GIX5Agent()
}

# Modelos de entrada para os endpoints
class SendMessageRequest(BaseModel):
    chat_id: str
    user_id: str  # Corrigido para texto, pois no DB é text
    message: str
    subject: str  # Deve ser um dos valores do ENUM "Chat_Subjects"

class CreateChatRequest(BaseModel):
    subject: str
    user_id: str  

@app.post("/createchat")
async def create_chat_endpoint(
    request: CreateChatRequest, 
    user=Depends(authenticate_request) if AUTENTICACAO_ATIVADA else None
):
    """Cria um novo chat e o armazena no banco."""
    chat_id = create_chat(request.subject, request.user_id)
    return {"chat_id": chat_id, "subject": request.subject}

@app.post("/sendmessage")
async def send_message(
    request: SendMessageRequest, 
    user=Depends(authenticate_request) if AUTENTICACAO_ATIVADA else None
):
    """Processa a mensagem do usuário, armazena no banco e responde usando o modelo correto."""
    
    print("🟢 Iniciando processamento da mensagem...")

    #  Salvar mensagem do usuário
    start_time = time.time()
    sender_type = "USER"
    save_message(request.chat_id, sender_type, request.message)
    print(f"✅ Mensagem do usuário salva! Tempo: {time.time() - start_time:.2f}s")

    # Buscar histórico do chat
    start_time = time.time()
    chat_history = get_chat_history(request.chat_id, limit=15)
    print(f"✅ Histórico carregado! Tempo: {time.time() - start_time:.2f}s")

    #  Verifica se o histórico veio vazio
    if not chat_history:
        print("❌ ERRO: O histórico do chat veio vazio!")
    
    #  Gerar resposta com IA
    start_time = time.time()
    response_text = agents[request.subject].answer_question(request.message, chat_history)
    print(f"✅ Resposta da IA gerada! Tempo: {time.time() - start_time:.2f}s")

    # 🔴 Verifica se a IA retornou algo
    if not response_text:
        print("❌ ERRO: A IA não gerou nenhuma resposta!")

    # 🟢 Etapa 4: Salvar resposta da IA
    start_time = time.time()
    save_message(request.chat_id, "AI", response_text)
    print(f"✅ Resposta da IA salva! Tempo: {time.time() - start_time:.2f}s")

    print("🚀 Processamento concluído com sucesso!")

    return {
        "chat_id": request.chat_id,
        "response": response_text
    }
