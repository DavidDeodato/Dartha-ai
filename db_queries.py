from database import get_connection
import uuid

def create_chat(subject, user_id, segment, name_chat, model=None):
    """Cria um novo chat baseado no segmento correto."""
    conn = get_connection(segment)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO "Chat" (id, name, subject, "AI", user_id, external_chat_id, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW()) 
                RETURNING id;
            """, (str(uuid.uuid4()), name_chat, subject, model if model else 'GPT_4_O', user_id, str(uuid.uuid4())))
            
            chat_id = cur.fetchone()["id"]
            conn.commit()
            return chat_id

    except Exception as e:
        print(f"❌ Erro ao criar chat: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def save_message(chat_id, sender_type, message, segment, file_name=None):
    """Salva uma mensagem no chat."""
    print(f"nome do arquivo: {file_name}")
    try:
        with get_connection(segment) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO "Message" (id, chat_id, "from", message, file_ids, created_at)
                    VALUES (gen_random_uuid(), %s, %s, %s, %s, NOW())
                    RETURNING id;
                    """,
                    (chat_id, sender_type, message, file_name if file_name else None),
                )
                message_id = cur.fetchone()["id"]
                conn.commit()
                return message_id
    except Exception as e:
        print(f"❌ Erro ao salvar mensagem: {e}")
        return None

def get_chat_history(chat_id, segment, limit=15):
    """Recupera as últimas mensagens de um chat específico baseado no segmento."""
    try:
        with get_connection(segment) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT message, "from", created_at
                    FROM "Message"
                    WHERE chat_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s;
                """, (chat_id, limit))
                
                messages = [{"message": row["message"], "sender": row["from"], "timestamp": row["created_at"]}
                            for row in cur.fetchall()]
                
                return messages
    except Exception as e:
        print(f"❌ Erro ao recuperar histórico do chat {chat_id}: {e}")
        return []
