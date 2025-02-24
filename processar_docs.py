import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")

# Definir caminho para os documentos e embeddings
MODEL_NAME = "GIX5"  # Nome do modelo atual
DOCS_PATH = f"docxs/{MODEL_NAME}/"
VECTORSTORE_PATH = f"embeddings/{MODEL_NAME}/"

# Criar diretório para armazenar embeddings, se não existir
os.makedirs(VECTORSTORE_PATH, exist_ok=True)

# Carregar os documentos DOCX
documents = []
for file in os.listdir(DOCS_PATH):
    if file.endswith(".docx"):
        loader = Docx2txtLoader(os.path.join(DOCS_PATH, file))
        documents.extend(loader.load())

# Verificar se carregamos documentos
if not documents:
    print("🚨 Nenhum documento foi carregado. Verifique se há arquivos em docxs/GIX5/")
    exit()

# Dividir os textos em chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
split_texts = text_splitter.split_documents(documents)

# Criar embeddings
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# Salvar no FAISS
vector_store = FAISS.from_documents(split_texts, embeddings)
vector_store.save_local(VECTORSTORE_PATH)

print(f"✅ Processamento concluído! {len(split_texts)} chunks salvos em {VECTORSTORE_PATH}")
