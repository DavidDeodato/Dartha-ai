from langchain_anthropic import ChatAnthropic
from langchain.schema import SystemMessage, HumanMessage
import os
from dotenv import load_dotenv

# Carregar variáveis do ambiente
load_dotenv()


# Defina sua chave da API
api_key = os.getenv("ANTHROPIC_API_KEY")

# Inicializa o modelo Claude 3.7 Sonnet via LangChain
chat = ChatAnthropic(model="claude-3-5-haiku-20241022", anthropic_api_key=api_key)


# Define o System Prompt
system_message = SystemMessage(content="Voce é um assistente muito rude, voce fala de forma muito rude e é mal educaco, voce vai assumir essa persona.")

# Define a pergunta do usuário
human_message = HumanMessage(content="Ou, me fala uma coisa. Qual é a cor do céu?")

# Faz a requisição ao modelo
response = chat.invoke([system_message, human_message])

# Exibe a resposta
print(response.content)
