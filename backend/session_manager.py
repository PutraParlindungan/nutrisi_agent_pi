from backend.database import get_db_connection
import time
import re

def get_all_sessions(user_id: int) -> list:
    """Menarik semua riwayat sesi milik pengguna."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cur:
            # Urutkan dari yang paling baru
            query = "SELECT session_id, session_name FROM sessions WHERE user_id = %s ORDER BY created_at DESC;"
            cur.execute(query, (user_id,))
            rows = cur.fetchall()
            return [{"session_id": r[0], "session_name": r[1]} for r in rows]
    except Exception as e:
        print(f"Error get_all_sessions: {e}")
        return []
    finally:
        conn.close()

def create_session(user_id: int, session_name: str):
    """Membuat sesi baru di database dan mengembalikan session_id (integer)."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            # Gunakan RETURNING untuk menangkap ID auto-increment dari Supabase
            query = "INSERT INTO sessions (user_id, session_name) VALUES (%s, %s) RETURNING session_id;"
            cur.execute(query, (user_id, session_name))
            new_session_id = cur.fetchone()[0]
            conn.commit()
            return new_session_id
    except Exception as e:
        print(f"Error create_session: {e}")
        return None
    finally:
        conn.close()

def delete_session(session_id: int):
    """Menghapus sesi dari database."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE session_id = %s;", (session_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error delete_session: {e}")
        return False
    finally:
        conn.close()

def save_message(session_id: int, sender_role: str, content: str) -> bool:
    """Menyimpan satu baris pesan ke database."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            query = "INSERT INTO message_history (session_id, sender_role, content) VALUES (%s, %s, %s);"
            cur.execute(query, (session_id, sender_role, content))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error save_message: {e}")
        return False
    finally:
        conn.close()

def get_session_messages(session_id: int, user_id: int) -> list:
    """Menarik riwayat obrolan dengan validasi user_id (Anti-IDOR)."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cur:
            query = """
                SELECT mh.sender_role, mh.content 
                FROM message_history mh
                JOIN sessions s ON mh.session_id = s.session_id
                WHERE s.session_id = %s AND s.user_id = %s 
                ORDER BY mh.created_at ASC;
            """
            cur.execute(query, (session_id, user_id))
            rows = cur.fetchall()
            return [{"role": r[0], "content": r[1]} for r in rows]
    except Exception as e:
        print(f"Error get_session_messages: {e}")
        return []
    finally:
        conn.close()

def extract_and_save_nutrition(user_id: int, ai_reply: str) -> int:
    saved_count = 0
    
    # Memecah setiap blok yang diawali dengan ikon 📋 sampai bertemu 📋 lagi atau 📊
    blok_makanan = re.findall(r"📋(.*?)(?=📋|📊|$)", ai_reply, re.DOTALL)
    
    if not blok_makanan:
        return 0

    conn = None
    try:
        waktu_mulai = time.time()
        print("\n[TEST DB] Membuka 1 koneksi database...")
        conn = get_db_connection()
        if not conn: return 0

        with conn.cursor() as cur:
            query = """
                INSERT INTO nutrition_logs (user_id, food_name, calories, protein, fat, carbs) 
                VALUES (%s, %s, %s, %s, %s, %s);
            """

            for blok_teks in blok_makanan:
                # Ambil baris pertama sebagai nama makanan, bersihkan bintang & sumber
                baris_pertama = blok_teks.strip().split('\n')[0]
                food_name = re.sub(r"[\*\#]", "", baris_pertama).split("(Sumber")[0].strip()
                
                # Pengaman ganda: lewati jika kebetulan menangkap "Total" atau kosong
                if "total" in food_name.lower() or not food_name:
                    continue

                cal_match = re.search(r"Kalori\s*:\s*([\d.]+)", blok_teks, re.IGNORECASE)
                pro_match = re.search(r"Protein\s*:\s*([\d.]+)", blok_teks, re.IGNORECASE)
                fat_match = re.search(r"Lemak\s*:\s*([\d.]+)", blok_teks, re.IGNORECASE)
                carb_match = re.search(r"Karbo\s*:\s*([\d.]+)", blok_teks, re.IGNORECASE)
                
                if cal_match:
                    calories = float(cal_match.group(1))
                    protein = float(pro_match.group(1)) if pro_match else 0.0
                    fat = float(fat_match.group(1)) if fat_match else 0.0
                    carbs = float(carb_match.group(1)) if carb_match else 0.0
                    
                    print(f"[TEST DB] ⏳ Menyimpan: {food_name}")
                    cur.execute(query, (user_id, food_name, calories, protein, fat, carbs))
                    saved_count += 1
            
            if saved_count > 0:
                print(f"[TEST DB] 💾 Melakukan COMMIT {saved_count} data sekaligus...")
                conn.commit()
            
        waktu_selesai = time.time()
        print(f"[TEST DB] Koneksi ditutup. Waktu total: {waktu_selesai - waktu_mulai:.4f} detik\n")
            
    except Exception as e:
        print(f"Error parsing food block: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()
        
    return saved_count


def log_missing_food(user_id: int, keyword: str) -> bool:
    """Mencatat makanan yang gagal dilacak API/Database ke dalam log untuk dievaluasi Admin."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            query = "INSERT INTO missing_foods_log (user_id, keyword) VALUES (%s, %s);"
            cur.execute(query, (user_id, keyword))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error log_missing_food: {e}")
        return False
    finally:
        conn.close()

def rename_session(session_id: int, new_name: str) -> bool:
    """Mengubah nama riwayat obrolan di database."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            query = "UPDATE sessions SET session_name = %s WHERE session_id = %s;"
            cur.execute(query, (new_name, session_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error rename_session: {e}")
        return False
    finally:
        conn.close()

