import os
from dotenv import load_dotenv
from langchain_openai import OpenAI

# Importações opcionais para RAG
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings

# Carregar variáveis do ambiente
load_dotenv()

class Financeiro:
    def __init__(self, api_key):
        """Inicializa o modelo 'FinanceiroAI' com o prompt de sistema definido."""

        # Definir API Key
        self.api_key = api_key

        # Configurar LLM principal
        self.llm = OpenAI(openai_api_key=api_key)

        # Variável para ativar/desativar manualmente o RAG
        self.usar_rag = True  

        # Caminho dos embeddings
        embeddings_path = "embeddings/FINANCEIRO"

        # Verifica se a pasta de embeddings está vazia ou não existe
        if not os.path.exists(embeddings_path) or not os.listdir(embeddings_path):
            print(f"⚠️ A pasta de embeddings '{embeddings_path}' está vazia ou não existe. Desativando RAG automaticamente.")
            self.usar_rag = False

        # Se usar_rag for True, inicializa FAISS
        if self.usar_rag:
            try:
                self.vector_store = FAISS.load_local(
                    embeddings_path,
                    OpenAIEmbeddings(openai_api_key=api_key),
                    allow_dangerous_deserialization=True
                )
                self.retriever = self.vector_store.as_retriever()
            except Exception as e:
                print(f"❌ Erro ao carregar os embeddings: {e}")
                self.usar_rag = False

    def answer_question(self, question: str, chat_history: list = None) -> str:
        """
        Gera uma resposta para a pergunta baseada no histórico do chat e no conhecimento embutido (com ou sem RAG).
        """
        # 1. Verifica se há histórico válido
        if not chat_history or not isinstance(chat_history, list):
            chat_history = []

        history_context = "\n".join(
            [msg["message"] for msg in chat_history if isinstance(msg, dict) and "message" in msg]
        ) if chat_history else "Sem histórico disponível."

        # 2. Se RAG estiver ativado, buscar documentos relevantes
        retrieved_docs = ""
        if self.usar_rag:
            relevant_docs = self.retriever.invoke(question)
            if relevant_docs:
                retrieved_docs = str(relevant_docs).replace("{", "{{").replace("}", "}}")

        # 3. Criar o prompt inicial integrando histórico, pergunta e documentos (se houver)
        formatted_input = f"""
⚡ Assistente Financeiro:
Histórico do chat:
{history_context}

Pergunta do usuário:
{question}

{"Documentos relevantes:\n" + retrieved_docs if self.usar_rag else ""}
"""

        # 4. Geração da resposta inicial
        initial_response = self.llm.invoke(formatted_input)

        # 5. Refinamento da resposta
        refine_prompt = f"""
Aqui está a resposta inicial:
---
{initial_response}
---
Agora, refine a resposta para que fique ainda mais clara, objetiva e didática.
"""
        refined_response = self.llm.invoke(refine_prompt)

        return refined_response
