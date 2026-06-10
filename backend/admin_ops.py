from backend.database import get_db_connection

def get_all_users():
    """Menarik semua data pengguna untuk tabel Dasbor Admin."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cur:
            query = """
                SELECT user_id, name, username, role, is_active, created_at 
                FROM users 
                ORDER BY created_at DESC;
            """
            cur.execute(query)
            rows = cur.fetchall()
            # Mapping agar header tabel Pandas nanti langsung rapi dalam bahasa Indonesia
            return [
                {
                    "ID": r[0], 
                    "Nama": r[1], 
                    "Username": r[2], 
                    "Role": r[3], 
                    "Status Aktif": r[4], 
                    "Tanggal Daftar": r[5]
                } 
                for r in rows
            ]
    except Exception as e:
        print(f"Error get_all_users: {e}")
        return []
    finally:
        conn.close()

def toggle_user_status(user_id: int, current_status: bool) -> bool:
    """Mengubah status is_active (Suspend/Unsuspend)."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            # Membalikkan logika boolean: Jika True jadi False, jika False jadi True
            new_status = not current_status
            query = "UPDATE users SET is_active = %s WHERE user_id = %s;"
            cur.execute(query, (new_status, user_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error toggle_user_status: {e}")
        return False
    finally:
        conn.close()

def delete_user_permanently(user_id: int) -> bool:
    """Menghapus akun pengguna secara permanen (ON DELETE CASCADE otomatis jalan)."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            query = "DELETE FROM users WHERE user_id = %s;"
            cur.execute(query, (user_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error delete_user_permanently: {e}")
        return False
    finally:
        conn.close()

def get_system_stats() -> dict:
    """Menghitung total pengguna, sesi, dan log makanan gagal."""
    conn = get_db_connection()
    stats = {"total_users": 0, "total_sessions": 0, "total_missing": 0}
    if not conn:
        return stats
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users;")
            stats["total_users"] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM sessions;")
            stats["total_sessions"] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM missing_foods_log;")
            stats["total_missing"] = cur.fetchone()[0]
            
        return stats
    except Exception as e:
        print(f"Error get_system_stats: {e}")
        return stats
    finally:
        conn.close()

def get_missing_foods_log() -> list:
    """Menarik log makanan yang gagal dilacak, di-join dengan tabel users."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cur:
            query = """
                SELECT m.id, u.username, m.keyword, m.created_at 
                FROM missing_foods_log m
                JOIN users u ON m.user_id = u.user_id
                ORDER BY m.created_at DESC;
            """
            cur.execute(query)
            rows = cur.fetchall()
            return [
                {
                    "Log ID": r[0], 
                    "Username": r[1], 
                    "Kata Kunci (Gagal)": r[2], 
                    "Waktu Kejadian": r[3]
                } 
                for r in rows
            ]
    except Exception as e:
        print(f"Error get_missing_foods_log: {e}")
        return []
    finally:
        conn.close()