import os
from dotenv import load_dotenv
from typing import List, Dict
import time
import sys
import re

# LangChain imports
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.chat_models import AzureChatOpenAI  # Alterado para Azure
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

# Carregar variáveis do ambiente
load_dotenv()

docs_str = ""

# Configuração do Azure OpenAI Foundry
AZURE_OPENAI_ENDPOINT = "https://pedro-m7w8u09u-eastus2.services.ai.azure.com/"
AZURE_OPENAI_API_KEY = "6V8h8sg9ODbUxVeDLDl6lTyQqupx7makDoZCReyTbVi6G68hp0KyJQQJ99BCACHYHv6XJ3w3AAAAACOGfgZf"
AZURE_OPENAI_DEPLOYMENT_NAME = "o1-mini"
AZURE_OPENAI_API_VERSION = "2023-07-01-preview"

# Função para logs formatados com cores ANSI
def log(message, color="\033[94m"):
    print(f"{color}{message}\033[0m")

# Definição do System Prompt
SYSTEM_PROMPT = """
Você é um assistente virtual altamente especializado no GIX5 (Gestão Integrada de Excelência) da X5 Business...
(sua descrição completa aqui)
"""

def clean_response(response: str) -> str:
    response = re.sub(r"^\s*Resposta:\s*", "", response, flags=re.IGNORECASE)
    return response.strip()

class GIX5Agent:
    def __init__(self, api_key):
        """Inicializa o agente carregando embeddings e criando as chains auxiliares."""
        self.api_key = api_key

        log("🟢 Iniciando carregamento dos embeddings...")
        start_time = time.time()
        self.vector_store = FAISS.load_local(
            "embeddings/GIX5",
            OpenAIEmbeddings(openai_api_key=api_key),
            allow_dangerous_deserialization=True
        )
        self.retriever = self.vector_store.as_retriever()
        log(f"✅ Embeddings carregados! Tempo: {time.time() - start_time:.2f}s", "\033[92m")

        # Instancia o LLM com Azure OpenAI
        self.llm = AzureChatOpenAI(
            openai_api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
            openai_api_key=AZURE_OPENAI_API_KEY,
            temperature=1
        )

        # Modelo auxiliar para classificar intenção da pergunta
        self.intent_classifier_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                template="""
Classifique a seguinte pergunta do usuário como uma das seguintes categorias:
- "NEEDS_RAG" → A pergunta exige consulta ao material do curso GIX5.
- "NO_RAG_CONTINUE" → A pergunta é apenas conversacional e não precisa de busca em documentos.
- "UNKNOWN" → Não é possível determinar.

Pergunta do usuário: {question}

Retorne apenas uma dessas categorias, sem explicações.
                """,
                input_variables=["question"]
            )
        )

    def format_chat_history(self, chat_history):
        formatted_history = []
        for msg in chat_history:
            if isinstance(msg, dict) and "message" in msg and "sender" in msg:
                if msg["sender"] == "USER":
                    formatted_history.append(HumanMessage(content=msg["message"]))
                elif msg["sender"] == "AI":
                    formatted_history.append(AIMessage(content=msg["message"]))
        return formatted_history

    def answer_question(self, question: str, chat_history: List[Dict] = None) -> str:
        log("🟢 Iniciando processamento da mensagem...")
        start_time = time.time()

        if chat_history is None:
            chat_history = []

        log("✅ Classificando intenção da pergunta...")
        intent = self.intent_classifier_chain.run(question=question).strip()
        log(f"🔹 Intenção detectada: {intent}")

        if intent == "NO_RAG_CONTINUE":
            log("✅ Pergunta identificada como conversacional, gerando resposta...")
            formatted_history = self.format_chat_history(chat_history)
            messages = [HumanMessage(content=SYSTEM_PROMPT)]
            messages.extend(formatted_history)
            messages.append(HumanMessage(content=question))
            response = self.llm.invoke(messages)
            log(f"✅ Resposta gerada! Tempo: {time.time() - start_time:.2f}s", "\033[92m")
            return clean_response(response.content)

        if intent == "NEEDS_RAG":
            log("✅ Necessário buscar informações no RAG...")
            relevant_docs = self.retriever.invoke(question)
            if not relevant_docs:
                log("⚠️ Nenhum documento relevante encontrado no RAG!", "\033[93m")
                return "Não encontrei informações no material do curso sobre isso."
            log(f"✅ {len(relevant_docs)} documentos relevantes encontrados!", "\033[92m")
            docs_str = "\n".join([doc.page_content for doc in relevant_docs]).strip()
            messages = [HumanMessage(content=SYSTEM_PROMPT), HumanMessage(content=f"🔹 Informações relevantes:\n{docs_str}"), HumanMessage(content=question)]
            response = self.llm.invoke(messages)
            log(f"✅ Resposta final gerada! Tempo: {time.time() - start_time:.2f}s", "\033[92m")
            return clean_response(response.content)

        log("⚠️ Intenção não identificada corretamente, retornando resposta padrão.", "\033[91m")
        return "Não consegui entender sua intenção. Você pode reformular sua pergunta?"
