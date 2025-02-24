from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAI
import os
from dotenv import load_dotenv

# Carregar variáveis do ambiente
load_dotenv()
OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")

class GIX5Agent:
    def __init__(self):
        """Inicializa o agente carregando os embeddings do curso GIX5."""
        self.vector_store = FAISS.load_local(
            "embeddings/GIX5",
            OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY),
            allow_dangerous_deserialization=True  # Permite carregamento seguro do FAISS
        )
        self.retriever = self.vector_store.as_retriever()
        self.llm = OpenAI(openai_api_key=OPENAI_API_KEY)

    def answer_question(self, question: str, chat_history: list) -> str:
        """Pipeline de resposta baseado no histórico do chat."""

        # ✅ Transforma o histórico de mensagens em texto legível
        history_context = "\n".join(
            [msg["message"] for msg in chat_history if isinstance(msg, dict) and "message" in msg]
        ) if chat_history else "Sem histórico disponível."

        # 🔹 Passo 1: Buscar informações relevantes nos embeddings
        relevant_docs = self.retriever.invoke(question)

        if not relevant_docs:
            return "Não encontrei informações no material do curso sobre isso."

        # 🔹 Passo 2: Gerar uma resposta baseada no material e no histórico
        formatted_input = f"""
        Histórico do chat:
        {history_context}

        Baseando-se no material do curso GIX5, responda com clareza e detalhes:
        {question}
        """
        initial_response = self.llm.invoke(formatted_input)

        # 🔹 Passo 3: Refinar a resposta para torná-la mais objetiva e compreensível
        refine_prompt = f"""
        Aqui está uma resposta inicial gerada sobre "{question}":
        ---
        {initial_response}
        ---
        Agora, reescreva a resposta para que fique mais clara, objetiva e didática, removendo redundâncias e melhorando a legibilidade.
        """
        refined_response = self.llm.invoke(refine_prompt)

        return refined_response