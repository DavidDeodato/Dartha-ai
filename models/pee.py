import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAI


# Carregar variáveis do ambiente
load_dotenv()


class PEEAgent:
    def __init__(self, api_key):
        """Inicializa o agente carregando os embeddings disponíveis dentro de PEE (PEX, PDC, PAF, PLX e Geral)."""
        
        # 📌 Diretório base dos embeddings
        base_path = "embeddings/PEE/"
        
        # 📌 Lista de subpastas esperadas
        subfolders = ["PEX", "PDC", "PAF", "PLX", "geral"]
        
        # 📌 Filtrar apenas as pastas que realmente contêm embeddings
        valid_paths = []
        for folder in subfolders:
            folder_path = os.path.join(base_path, folder)
            if os.path.exists(folder_path) and os.path.isfile(os.path.join(folder_path, "index.faiss")):
                valid_paths.append(folder_path)

        # 📌 Se não houver embeddings disponíveis, lançar erro
        if not valid_paths:
            raise ValueError("❌ Nenhuma pasta de embeddings válida encontrada para PEE. Verifique se os embeddings foram gerados.")

        # 📌 Carregar todos os embeddings disponíveis
        self.vector_stores = []
        for path in valid_paths:
            try:
                store = FAISS.load_local(path, OpenAIEmbeddings(openai_api_key=api_key), allow_dangerous_deserialization=True)
                self.vector_stores.append(store)
            except Exception as e:
                print(f"⚠️ Erro ao carregar embeddings de {path}: {e}")

        # 📌 Criar um único retriever que busca em todas as bases carregadas
        if not self.vector_stores:
            raise ValueError("❌ Não foi possível carregar nenhum embedding válido para PEE.")
        
        self.retrievers = [store.as_retriever() for store in self.vector_stores]
        self.llm = OpenAI(openai_api_key=api_key)

    def answer_question(self, question: str, chat_history: list = None) -> str:
        """
        Gera uma resposta para a pergunta baseada no histórico do chat e nos materiais disponíveis dos cursos PEX, PDC, PAF, PLX e Geral.
        O fluxo é:
          1. Verificação do histórico do chat (se existir).
          2. Busca nos embeddings disponíveis.
          3. Geração de uma resposta inicial com o contexto.
          4. Refinamento da resposta para torná-la mais clara e didática.
        """
        if not chat_history or not isinstance(chat_history, list):
            chat_history = []

        # 🔹 Formatar histórico do chat
        history_context = "\n".join([msg["message"] for msg in chat_history if isinstance(msg, dict) and "message" in msg]) if chat_history else "Sem histórico disponível."

        # 🔹 Buscar informações relevantes nos embeddings
        relevant_docs = []
        for retriever in self.retrievers:
            relevant_docs.extend(retriever.invoke(question))

        if not relevant_docs:
            return "Não encontrei informações nos materiais dos cursos PEX, PDC, PAF e PLX sobre isso."

        # 🔹 Converter documentos relevantes para string e evitar conflitos no f-string
        docs_str = str(relevant_docs).replace("{", "{{").replace("}", "}}")

        # 🔹 Criar prompt inicial com histórico + contexto + documentos
        formatted_input = f"""
Histórico do chat:
{history_context}

Baseando-se nos materiais disponíveis dos cursos PEX, PDC, PAF, PLX e Geral, responda com clareza e detalhes a seguinte pergunta:
{question}

Documentos relevantes:
{docs_str}
"""
        # 🔹 Gerar resposta inicial com o LLM
        initial_response = self.llm.invoke(formatted_input)

        # 🔹 Criar prompt de refinamento para melhorar a resposta inicial
        refine_prompt = f"""
Aqui está uma resposta inicial gerada para a pergunta "{question}":
---
{initial_response}
---
Agora, reescreva a resposta para que fique mais clara, objetiva e didática, removendo redundâncias e melhorando a legibilidade.
"""
        refined_response = self.llm.invoke(refine_prompt)

        return refined_response
