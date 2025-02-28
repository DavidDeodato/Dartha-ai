import os
import pdfplumber
import pytesseract
from PIL import Image
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain.schema import Document  # 📌 Importação crucial

# Carregar variáveis do ambiente
load_dotenv()
OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")

# 📌 Configuração do Tesseract OCR (para PDFs baseados em imagem)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 📌 Passo 1: Selecionar Modelo Principal
DOCS_BASE_PATH = "docxs/"
models = [m for m in os.listdir(DOCS_BASE_PATH) if os.path.isdir(os.path.join(DOCS_BASE_PATH, m))]

if not models:
    print("🚨 Nenhum modelo encontrado em 'docxs/'. Verifique os diretórios.")
    exit()

print("\n📌 Modelos disponíveis:")
for i, model in enumerate(models):
    print(f"{i+1}. {model}")

model_index = int(input("\nSelecione o número do modelo desejado: ")) - 1
MODEL_NAME = models[model_index]

# 📌 Passo 2: Verificar se há submodelos
MODEL_PATH = os.path.join(DOCS_BASE_PATH, MODEL_NAME)
submodels = [s for s in os.listdir(MODEL_PATH) if os.path.isdir(os.path.join(MODEL_PATH, s))]

if MODEL_NAME == "PEE":  # Adicionar a opção "geral" apenas para PEE
    submodels.append("geral")

if submodels:
    print("\n📌 Submodelos disponíveis:")
    for i, submodel in enumerate(submodels):
        print(f"{i+1}. {submodel}")

    submodel_index = int(input("\nSelecione o número do submodelo desejado: ")) - 1
    MODEL_NAME = os.path.join(MODEL_NAME, submodels[submodel_index])

# 📌 Atualizar caminhos após seleção
DOCS_PATH = os.path.join(DOCS_BASE_PATH, MODEL_NAME)
VECTORSTORE_PATH = f"embeddings/{MODEL_NAME}/"

# Criar diretório para armazenar embeddings, se não existir
os.makedirs(VECTORSTORE_PATH, exist_ok=True)

# 📌 Passo 3: Listar documentos disponíveis e selecionar quais processar
all_documents = [file for file in os.listdir(DOCS_PATH) if file.endswith((".docx", ".pdf"))]

if not all_documents:
    print(f"🚨 Nenhum documento .docx ou .pdf encontrado em {DOCS_PATH}. Verifique os arquivos.")
    exit()

print("\n📌 Documentos disponíveis:")
for i, doc in enumerate(all_documents):
    print(f"{i+1}. {doc}")

doc_selection = input("\nDigite os números dos documentos que deseja processar (ex: 1,2,3) ou 'todos': ").strip()

if doc_selection.lower() == "todos":
    selected_documents = all_documents
else:
    indices = [int(i) - 1 for i in doc_selection.split(",")]
    selected_documents = [all_documents[i] for i in indices]

# 📌 Passo 4: Carregar documentos e tratar PDFs e DOCX corretamente
documents = []

def extract_text_from_pdf(pdf_path):
    """Tenta extrair texto de um PDF. Se não conseguir, usa OCR."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"
    
    if not text.strip():  # Se o PDF não for copiável, aplicar OCR
        print(f"🔍 Aplicando OCR no PDF: {pdf_path}")
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                img = page.to_image()
                text += pytesseract.image_to_string(img.original) + "\n"
    
    return text.strip() if text.strip() else "⚠️ OCR não conseguiu extrair o texto."

for file in selected_documents:
    file_path = os.path.join(DOCS_PATH, file)

    if file.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
        documents.extend(loader.load())

    elif file.endswith(".pdf"):
        pdf_text = extract_text_from_pdf(file_path)
        if pdf_text:
            documents.append(Document(page_content=pdf_text))  # 📌 Correção aqui

# Verificar se carregamos documentos
if not documents:
    print("🚨 Nenhum documento carregado. Algo deu errado.")
    exit()

# 📌 Passo 5: Processar documentos e gerar embeddings
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
split_texts = text_splitter.split_documents(documents)

# Criar embeddings
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# Salvar no FAISS
vector_store = FAISS.from_documents(split_texts, embeddings)
vector_store.save_local(VECTORSTORE_PATH)

print(f"\n✅ Processamento concluído! {len(split_texts)} chunks salvos em {VECTORSTORE_PATH}") 
