import psycopg
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Pegando a URL do banco de dados do .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ ERRO: A variável DATABASE_URL não foi encontrada no .env!")

# Criando a conexão com o PostgreSQL
def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def diagnose_message_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            print("\n🔍 **INICIANDO DIAGNÓSTICO COMPLETO DA TABELA 'Message'** 🔍")

            # 1️⃣ Verificar se a tabela 'Message' existe
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'Message'
                );
            """)
            table_exists = cur.fetchone()["exists"]
            print(f"🛠️ Tabela 'Message' existe? {table_exists}")

            if not table_exists:
                print("❌ ERRO: A tabela 'Message' NÃO existe! O código não pode funcionar.")
                return

            # 2️⃣ Listar todas as colunas, tipos de dados e se aceitam NULL
            cur.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'Message';
            """)
            columns = cur.fetchall()
            print("\n📌 Estrutura da tabela 'Message':")
            for col in columns:
                print(f"   - {col['column_name']} ({col['data_type']}) - NULLABLE: {col['is_nullable']}")

            # 3️⃣ Verificar se alguma coluna tem um DEFAULT configurado
            cur.execute("""
                SELECT column_name, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'Message' AND column_default IS NOT NULL;
            """)
            defaults = cur.fetchall()
            print("\n⚙️ Colunas com DEFAULT configurado:")
            for default in defaults:
                print(f"   - {default['column_name']}: {default['column_default']}")

            # 4️⃣ Testar um INSERT com dados fictícios
            try:
                cur.execute("""
                    INSERT INTO "Message" (id, chat_id, message, created_at)
                    VALUES (gen_random_uuid(), 'chat_teste', 'Mensagem de teste', NOW())
                    RETURNING id;
                """)
                message_id = cur.fetchone()["id"]
                conn.commit()
                print(f"\n✅ Teste de INSERT bem-sucedido! ID da nova mensagem: {message_id}")

                # 5️⃣ Buscar a última mensagem salva para confirmar a inserção
                cur.execute("""
                    SELECT * FROM "Message" ORDER BY created_at DESC LIMIT 1;
                """)
                last_message = cur.fetchone()
                print("\n🔍 Última mensagem salva na tabela 'Message':")
                print(last_message)
            except Exception as e:
                print(f"\n❌ ERRO ao inserir uma mensagem: {e}")
                conn.rollback()

            print("\n✅ **DIAGNÓSTICO FINALIZADO** ✅")

# Executa o diagnóstico
diagnose_message_table()
