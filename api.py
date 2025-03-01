import os
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from database import get_connection
from db_queries import create_chat, save_message, get_chat_history
from auth import authenticate_request
import time
from config import SEGMENT_CONFIG

AUTENTICACAO_ATIVADA = False

app = FastAPI()

#testezinho
@app.get("/")
def read_root():
    return {"Hello": "API Online!"}

class SendMessageRequest(BaseModel):
    chat_id: str
    user_id: str
    message: str
    subject: str
    segment: str

class CreateChatRequest(BaseModel):
    subject: str
    user_id: str
    segment: str

@app.post("/createchat")
async def create_chat_endpoint(
    request: CreateChatRequest,
    user=Depends(authenticate_request) if AUTENTICACAO_ATIVADA else None
):
    if request.segment not in SEGMENT_CONFIG:
        return {"error": f"Segmento inválido: {request.segment}"}

    if request.subject not in SEGMENT_CONFIG[request.segment]["models"]:
        return {"error": f"O modelo '{request.subject}' não está disponível no segmento '{request.segment}'."}

    chat_id = create_chat(request.subject, request.user_id, request.segment)
    return {"chat_id": chat_id, "subject": request.subject, "segment": request.segment}

@app.post("/sendmessage")
async def send_message(
    request: SendMessageRequest,
    user=Depends(authenticate_request) if AUTENTICACAO_ATIVADA else None
):
    print("🟢 Iniciando processamento da mensagem...")

    if request.segment not in SEGMENT_CONFIG:
        return {"error": f"Segmento inválido: {request.segment}"}

    if request.subject not in SEGMENT_CONFIG[request.segment]["models"]:
        return {"error": f"O modelo '{request.subject}' não está disponível no segmento '{request.segment}'."}

    # 🔹 Criar o agente dinamicamente com a API Key correta
    api_key = SEGMENT_CONFIG[request.segment]["api_key"]
    agent = SEGMENT_CONFIG[request.segment]["models"][request.subject](api_key)

    # Salvar mensagem do usuário
    start_time = time.time()
    sender_type = "USER"
    save_message(request.chat_id, sender_type, request.message, request.segment)
    print(f"✅ Mensagem do usuário salva! Tempo: {time.time() - start_time:.2f}s")

    # Buscar histórico do chat
    start_time = time.time()
    chat_history = get_chat_history(request.chat_id, request.segment, limit=15)
    print(f"✅ Histórico carregado! Tempo: {time.time() - start_time:.2f}s")

    if not chat_history:
        print("❌ ERRO: O histórico do chat veio vazio!")
    
    # Gerar resposta com IA
    start_time = time.time()
    response_text = agent.answer_question(request.message, chat_history)
    print(f"✅ Resposta da IA gerada! Tempo: {time.time() - start_time:.2f}s")

    if not response_text:
        print("❌ ERRO: A IA não gerou nenhuma resposta!")

    # Salvar resposta da IA
    start_time = time.time()
    save_message(request.chat_id, "AI", response_text, request.segment)
    print(f"✅ Resposta da IA salva! Tempo: {time.time() - start_time:.2f}s")

    print("🚀 Processamento concluído com sucesso!")

    return {
        "chat_id": request.chat_id,
        "response": response_text
    }
