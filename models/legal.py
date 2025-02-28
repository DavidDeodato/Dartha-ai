import os
from dotenv import load_dotenv
from langchain_openai import OpenAI

# Carregar variáveis do ambiente
load_dotenv()
OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")

class LegalAI:
    def __init__(self):
        """Inicializa o modelo jurídico, focado em consultas sobre direito e legislação."""
        self.llm = OpenAI(openai_api_key=OPENAI_API_KEY)

    def answer_question(self, question: str, chat_history: list = None) -> str:
        """
        Gera uma resposta para questões jurídicas usando um prompt estruturado.
        O fluxo é:
          1. Recebe a pergunta do usuário e o histórico do chat.
          2. Formata a entrada de acordo com a necessidade jurídica.
          3. Gera uma resposta baseada na legislação vigente.
          4. Refinamento da resposta para maior clareza e precisão.
        """
        # Verifica se há histórico válido
        if not chat_history or not isinstance(chat_history, list):
            chat_history = []

        # Formatar o histórico de chat (mas apenas se for passado no endpoint)
        history_context = "\n".join(
            [msg["message"] for msg in chat_history if isinstance(msg, dict) and "message" in msg]
        ) if chat_history else ""

        # Criando um prompt estruturado para perguntas jurídicas
        legal_prompt = (
            "Você é um assistente jurídico especializado em leis brasileiras e internacionais. "
            "Seu objetivo é fornecer respostas claras, objetivas e baseadas na legislação vigente.\n\n"
            "⚖️ Contexto:\n"
        )
        
        if history_context:
            legal_prompt += f"Histórico da conversa:\n{history_context}\n\n"

        legal_prompt += f'O usuário fez a seguinte pergunta:\n"{question}"\n\n'
        legal_prompt += (
            "📌 Diretrizes para sua resposta:\n"
            "- Forneça uma explicação clara e objetiva.\n"
            "- Cite a base legal relevante, se aplicável.\n"
            "- Caso a questão seja muito específica ou dependa de análise aprofundada, informe que a resposta pode variar conforme o caso.\n\n"
            "Agora, elabore uma resposta detalhada:"
        )

        # Gera resposta inicial
        initial_response = self.llm.invoke(legal_prompt)

        # Refinamento da resposta
        refine_prompt = f"""
Aqui está a resposta inicial para a pergunta jurídica:
---
{initial_response}
---
Agora, refine a resposta para que fique ainda mais clara, objetiva e alinhada com as leis e normas vigentes.
"""
        refined_response = self.llm.invoke(refine_prompt)

        return refined_response
