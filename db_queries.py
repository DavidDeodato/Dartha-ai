import psycopg
from database import get_connection
import psycopg2
import uuid

# Criar um novo chat no banco de dados
import uuid

def create_chat(subject, user_id):
    conn = get_connection()  # Obtém a conexão corretamente
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO "Chat" (id, subject, user_id, external_chat_id, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, NOW(), NOW()) 
                RETURNING id;
            """, (str(uuid.uuid4()), subject, user_id, str(uuid.uuid4())))  # Gerando UUID para id e external_chat_id
            
            chat_id = cur.fetchone()["id"]  # Pega o ID corretamente usando dict_row
            conn.commit()
            return chat_id  # Retorna o ID da conversa criada

    except Exception as e:
        print(f"❌ Erro ao criar chat: {e}")
        conn.rollback()  # Se der erro, desfaz a transação
        return None
    finally:
        conn.close()  # Fecha a conexão corretamente

        
# Salvar mensagem no banco de dados
def save_message(chat_id, sender_type, message):
    """Salva uma mensagem no chat."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO "Message" (id, chat_id, "from", message, created_at)
                    VALUES (gen_random_uuid(), %s, %s, %s, NOW())
                    RETURNING id;
                    """,
                    (chat_id, sender_type, message),
                )
                message_id = cur.fetchone()["id"]  # Obtém o ID da mensagem salva
                conn.commit()
                return message_id
    except Exception as e:
        print(f"❌ Erro ao salvar mensagem: {e}")
        return None  # Retorna None para indicar falha


# Buscar histórico do chat
def get_chat_history(chat_id, limit=15):
    """Recupera as últimas mensagens de um chat específico de forma eficiente."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT message, "from", created_at
                    FROM "Message"
                    WHERE chat_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s;
                """, (chat_id, limit))
                
                # Retorna uma lista de dicionários com as mensagens
                messages = [{"message": row["message"], "sender": row["from"], "timestamp": row["created_at"]}
                            for row in cur.fetchall()]
                
                return messages
    except Exception as e:
        print(f"❌ Erro ao recuperar histórico do chat {chat_id}: {e}")
        return []  # Retorna uma lista vazia para evitar travamentos