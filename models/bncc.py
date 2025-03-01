import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAI


# Carregar variáveis do ambiente
load_dotenv()


class BNCCAgent:
    def __init__(self, api_key):

        # - pegando a chave api do openai
        self.api_key = api_key

        """Inicializa o agente BNCC carregando os embeddings extraídos do documento BNCC."""
        self.vector_store = FAISS.load_local(
            "embeddings/BNCC",
            OpenAIEmbeddings(openai_api_key=api_key),
            allow_dangerous_deserialization=True  # Permite carregamento seguro do FAISS
        )
        self.retriever = self.vector_store.as_retriever()
        self.llm = OpenAI(openai_api_key=api_key)

    def answer_question(self, question: str, chat_history: list = None) -> str:
        """
        Gera uma resposta para perguntas baseadas no conteúdo da BNCC.
        O fluxo é:
          1. Busca nos embeddings do documento BNCC.
          2. Gera uma resposta inicial com o contexto.
          3. Refinamento da resposta para torná-la mais clara e didática.
        """
        # 1. Recupera documentos relevantes
        relevant_docs = self.retriever.invoke(question)
        if not relevant_docs:
            return "Não encontrei informações sobre essa questão na BNCC."

        # Converter os documentos relevantes para string e ESCAPAR chaves para evitar conflitos no f-string
        docs_str = str(relevant_docs).replace("{", "{{").replace("}", "}}")

        # 2. Criação do prompt inicial integrando a pergunta e os documentos
        formatted_input = f"""
Baseando-se no documento oficial da BNCC, responda com clareza e detalhes a seguinte pergunta:
{question}

Documentos relevantes:
{docs_str}
"""
        # Chama o LLM para gerar uma resposta inicial com base no prompt formatado
        initial_response = self.llm.invoke(formatted_input)

        # 3. Criação do prompt de refinamento para melhorar a resposta inicial
        refine_prompt = f"""
Aqui está uma resposta inicial gerada para a pergunta "{question}":
---
{initial_response}
---
Agora, refine a resposta para que fique ainda mais clara, objetiva e alinhada com as diretrizes da BNCC.
"""
        refined_response = self.llm.invoke(refine_prompt)

        return refined_response
