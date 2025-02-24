import os
import docx
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")

# Caminho dos arquivos .docx
DOCS_PATH = "pdfs"  # Mesma pasta onde estavam os PDFs

# Lista os arquivos .docx na pasta
arquivos_docx = [f for f in os.listdir(DOCS_PATH) if f.endswith(".docx")]

if not arquivos_docx:
    print("⚠️ Nenhum arquivo .docx encontrado na pasta 'pdfs/'. Verifique os arquivos.")
    exit()

# Lê o conteúdo dos arquivos .docx
documentos = []
for arquivo in arquivos_docx:
    doc_path = os.path.join(DOCS_PATH, arquivo)
    doc = docx.Document(doc_path)

    # Extrai o texto do documento inteiro
    texto = "\n".join([paragrafo.text for paragrafo in doc.paragraphs])
    
    documentos.append({"nome": arquivo, "texto": texto})

# Divide o texto em pedaços menores (chunks)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
split_texts = []
for doc in documentos:
    chunks = text_splitter.split_text(doc["texto"])
    for chunk in chunks:
        split_texts.append({"texto": chunk, "origem": doc["nome"]})

# Verifica se extração foi bem-sucedida
if not split_texts:
    print("⚠️ Nenhum texto foi extraído! Verifique os arquivos.")
    exit()

# Transforma os textos em embeddings
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vector_store = FAISS.from_texts([t["texto"] for t in split_texts], embeddings)

# Salva os embeddings localmente
vector_store.save_local("vectorstore_faiss")

print(f"✅ Processamento concluído! {len(split_texts)} chunks salvos no banco de vetores.")
