from database import get_connection

def test_db():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                result = cur.fetchone()
                print("✅ Conexão com o banco de dados bem-sucedida!", result)
    except Exception as e:
        print("❌ Erro na conexão com o banco:", e)

if __name__ == "__main__":
    test_db()
