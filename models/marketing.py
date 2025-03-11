import os
from dotenv import load_dotenv
from langchain_openai import OpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings


# Carregar variáveis do ambiente
load_dotenv()

class Marketing:
    def __init__(self, api_key):
        """Inicializa o modelo 'Marketing' com o prompt de sistema definido."""

        # Definir API Key
        self.api_key = api_key

        # Configurar LLM principal
        self.llm = OpenAI(openai_api_key=api_key)

        # Variável para ativar/desativar manualmente o RAG
        self.usar_rag = True  

        # Caminho dos embeddings
        self.embeddings_path = "embeddings/MARKETING"

        # Verifica se a pasta de embeddings está vazia ou não existe
        if not os.path.exists(self.embeddings_path) or not os.listdir(self.embeddings_path):
            print(f"⚠️ A pasta de embeddings '{self.embeddings_path}' está vazia ou não existe. Desativando RAG automaticamente.")
            self.usar_rag = False

        # Se usar_rag for True, inicializa FAISS
        if self.usar_rag:
            try:
                self.vector_store = FAISS.load_local(
                    self.embeddings_path,
                    OpenAIEmbeddings(openai_api_key=api_key),
                    allow_dangerous_deserialization=True
                )
                self.retriever = self.vector_store.as_retriever()
            except Exception as e:
                print(f"❌ Erro ao carregar os embeddings: {e}")
                self.usar_rag = False

    def answer_question(self, question: str, chat_history: list = None) -> str:
        """Gera uma resposta baseada no histórico do chat e no conhecimento embutido (com ou sem RAG)."""

        # 1. Verifica se há histórico válido
        if not chat_history or not isinstance(chat_history, list):
            chat_history = []

        history_context = "\n".join(
            [msg["message"] for msg in chat_history if isinstance(msg, dict) and "message" in msg]
        ) if chat_history else "Sem histórico disponível."

        # 2. Se RAG estiver ativado, buscar documentos relevantes
        retrieved_docs = ""
        if self.usar_rag:
            try:
                relevant_docs = self.retriever.invoke(question)
                if relevant_docs:
                    retrieved_docs = "\n".join([doc.page_content for doc in relevant_docs])
            except Exception as e:
                print(f"⚠️ Erro ao recuperar documentos do RAG: {e}")
                self.usar_rag = False

        # 3. Criar o prompt inicial corretamente formatado
        formatted_input = f"""
🔹 Marketing Assistente:
Histórico do chat:
{history_context}

Pergunta do usuário:
{question}
"""

        # Adiciona os documentos relevantes apenas se RAG estiver ativado e se houver algo recuperado
        if self.usar_rag and retrieved_docs:
            formatted_input += f"\n\nDocumentos relevantes:\n{retrieved_docs}"

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
