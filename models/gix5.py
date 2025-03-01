import os
from dotenv import load_dotenv

# Importações para embeddings e vector store
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
# Importação para o LLM (usando a classe OpenAI, conforme o código antigo)
from langchain_openai import OpenAI



# Carregar variáveis do ambiente
load_dotenv()


class GIX5Agent:
    def __init__(self, api_key):

        # - pegando a chave api do openai
        self.api_key = api_key

        """Inicializa o agente carregando os embeddings do curso GIX5."""
        self.vector_store = FAISS.load_local(
            "embeddings/GIX5",
            OpenAIEmbeddings(openai_api_key=api_key),
            allow_dangerous_deserialization=True  # Permite carregamento seguro do FAISS
        )
        self.retriever = self.vector_store.as_retriever()
        # Usando o mesmo LLM do código antigo para garantir o uso do contexto
        self.llm = OpenAI(openai_api_key=api_key)

    def answer_question(self, question: str, chat_history: list = None) -> str:
        """
        Gera uma resposta para a pergunta baseada no histórico do chat e no material do curso GIX5.
        O fluxo é:
          1. Formatação do histórico do chat (se existir).
          2. Recuperação de documentos relevantes com base na pergunta.
          3. Geração de uma resposta inicial com o contexto.
          4. Refinamento da resposta para torná-la mais clara e didática.
        """
        # 1. Verifica se há histórico válido no request
        if not chat_history or not isinstance(chat_history, list):
            chat_history = []

        # Formatação do histórico do chat (se existir)
        history_context = "\n".join(
            [msg["message"] for msg in chat_history if isinstance(msg, dict) and "message" in msg]
        ) if chat_history else "Sem histórico disponível."

        # 2. Recupera documentos relevantes (para enriquecer o prompt)
        relevant_docs = self.retriever.invoke(question)
        if not relevant_docs:
            return "Não encontrei informações no material do curso sobre isso."

        # Converter os documentos relevantes para string e ESCAPAR chaves para evitar conflitos no f-string
        docs_str = str(relevant_docs).replace("{", "{{").replace("}", "}}")

        # 3. Criação do prompt inicial integrando o histórico, a pergunta e os documentos
        formatted_input = f"""
Histórico do chat:
{history_context}

Baseando-se no material do curso GIX5, responda com clareza e detalhes a seguinte pergunta:
{question}

Documentos relevantes:
{docs_str}
"""
        # Chama o LLM para gerar uma resposta inicial com base no prompt formatado
        initial_response = self.llm.invoke(formatted_input)

        # 4. Criação do prompt de refinamento para melhorar a resposta inicial
        refine_prompt = f"""
Aqui está uma resposta inicial gerada para a pergunta "{question}":
---
{initial_response}
---
Agora, reescreva a resposta para que fique mais clara, objetiva e didática, removendo redundâncias e melhorando a legibilidade.
"""
        refined_response = self.llm.invoke(refine_prompt)

        return refined_response
