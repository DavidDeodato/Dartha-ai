import os
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from database import get_connection
from db_queries import create_chat, save_message, get_chat_history
from auth import authenticate_request
import time
from config import SEGMENT_CONFIG
from fastapi.middleware.cors import CORSMiddleware

AUTENTICACAO_ATIVADA = False

app = FastAPI()

# - desativando restrições para todos (cors) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dartha.online",  # Domínio principal
        "https://dartha.ai",  # Outro domínio permitido
        "http://127.0.0.1:8000",  # Para testes locais
        "http://localhost:3000",  # Localhost na porta 3000 (React, Next.js, etc.)
        "http://localhost:3001",  # Localhost na porta 3001 (Outro frontend)
        "http://189.201.201.2",  # Seu IP público
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Permite todos os headers necessários
)
# ---------------------------------------

@app.get("/")
def read_root():
    return {"Hello": "API Online!"}

class SendMessageRequest(BaseModel):
    chat_id: str
    user_id: str
    message: str
    subject: str
    segment: str
    file_name: str

class CreateChatRequest(BaseModel):
    subject: str
    user_id: str
    segment: str
    name_chat: str
    model: str

## valores aceitos em model: O3-MINI, GPT_4_O, CLAUDE_3_5, CLAUDE_3_7


@app.post("/createchat")
async def create_chat_endpoint(
    request: CreateChatRequest,
    user=Depends(authenticate_request) if AUTENTICACAO_ATIVADA else None
):
    # 🚨 Coletar todos os erros possíveis 🚨
    errors = []


    if not request.name_chat:
        errors.append({"error": "Campo obrigatório ausente", "details": "O campo 'name_chat' é obrigatório."})

    if not request.user_id:
        errors.append({"error": "Campo obrigatório ausente", "details": "O campo 'user_id' é obrigatório."})
    
    if not request.subject:
        errors.append({"error": "Campo obrigatório ausente", "details": "O campo 'subject' é obrigatório."})

    if not request.segment:
        errors.append({"error": "Campo obrigatório ausente", "details": "O campo 'segment' é obrigatório."})

    if request.segment and request.segment not in SEGMENT_CONFIG:
        errors.append({"error": "Segmento inválido", "details": f"O segmento '{request.segment}' não é suportado."})

    if request.subject and request.segment in SEGMENT_CONFIG and request.subject not in SEGMENT_CONFIG[request.segment]["models"]:
        errors.append({"error": "Modelo não disponível", "details": f"O modelo '{request.subject}' não está disponível no segmento '{request.segment}'."})

    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    try:
        chat_id = create_chat(request.subject, request.user_id, request.segment, request.name_chat, request.model)
        if not chat_id:
            raise HTTPException(status_code=500, detail={"error": "Erro interno do servidor", "details": "Ocorreu um erro ao criar o chat."})

        return {"chat_id": chat_id, "subject": request.subject, "segment": request.segment, "name_chat": request.name_chat, "model": request.model}

    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Erro interno do servidor", "details": str(e)})

@app.post("/sendmessage")
async def send_message(
    request: SendMessageRequest,
    user=Depends(authenticate_request) if AUTENTICACAO_ATIVADA else None
):
    print("🟢 Iniciando processamento da mensagem...")

    # 🚨 Coletar todos os erros possíveis 🚨
    errors = []

    if not request.chat_id:
        errors.append({"error": "Campo obrigatório ausente", "details": "O campo 'chat_id' é obrigatório."})

    if not request.user_id:
        errors.append({"error": "Campo obrigatório ausente", "details": "O campo 'user_id' é obrigatório."})

    if not request.message:
        errors.append({"error": "Mensagem vazia", "details": "A IA não pode responder a uma mensagem vazia."})

    if len(request.message) > 2000:
        errors.append({"error": "Mensagem muito longa", "details": "A mensagem ultrapassou o limite de 2000 caracteres."})

    if not request.subject:
        errors.append({"error": "Campo obrigatório ausente", "details": "O campo 'subject' é obrigatório."})

    if not request.segment:
        errors.append({"error": "Campo obrigatório ausente", "details": "O campo 'segment' é obrigatório."})

    if request.segment and request.segment not in SEGMENT_CONFIG:
        errors.append({"error": "Segmento inválido", "details": f"O segmento '{request.segment}' não é suportado."})

    if request.subject and request.segment in SEGMENT_CONFIG and request.subject not in SEGMENT_CONFIG[request.segment]["models"]:
        errors.append({"error": "Modelo não disponível", "details": f"O modelo '{request.subject}' não está disponível no segmento '{request.segment}'."})

    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    # Criar o agente dinamicamente com a API Key correta
    api_key = SEGMENT_CONFIG[request.segment]["api_key"]
    agent = SEGMENT_CONFIG[request.segment]["models"][request.subject](api_key)

    print(f'nome do arquivo porra: {request.file_name}')

    try:
        # Salvar mensagem do usuário
        start_time = time.time()
        sender_type = "USER"
        save_message(request.chat_id, sender_type, request.message, request.segment, request.file_name if request.file_name else None)
        print(f"✅ Mensagem do usuário salva! Tempo: {time.time() - start_time:.2f}s \033[92m")

        # Buscar histórico do chat
        start_time = time.time()
        chat_history = get_chat_history(request.chat_id, request.segment, limit=15)
        print(f"✅ Histórico carregado! Tempo: {time.time() - start_time:.2f}s \033[92m")

        if not chat_history:
            print("❌ ERRO: O histórico do chat veio vazio!")

        # Gerar resposta com IA
        start_time = time.time()
        response_text = agent.answer_question(request.message, chat_history)
        print(f"✅ Resposta da IA gerada! Tempo: {time.time() - start_time:.2f}s", "\033[92m")

        if not response_text:
            raise HTTPException(status_code=500, detail={"error": "Erro na IA", "details": "A IA não conseguiu gerar uma resposta."})

        # Salvar resposta da IA
        start_time = time.time()
        save_message(request.chat_id, "AI", response_text, request.segment)
        print(f"✅ Resposta da IA salva! Tempo: {time.time() - start_time:.2f}s \033[92m")


        # verificando se o file_name foi passado -- caso passado - mandar para sav
            

        print("🚀 Processamento concluído com sucesso!")

        return {
            "chat_id": request.chat_id,
            "response": response_text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Erro interno do servidor", "details": str(e)})
