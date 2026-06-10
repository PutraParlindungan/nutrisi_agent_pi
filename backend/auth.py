import re
import bcrypt
from backend.database import get_db_connection

def hash_password(password: str) -> str:
    """Mengenkripsi kata sandi menggunakan algoritma bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Memverifikasi input kata sandi dengan hash yang tersimpan di database."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def register_user(name: str, username: str, password: str, role: str = 'user') -> dict:
    """
    Mendaftarkan pengguna baru ke database PostgreSQL.
    Mencegah duplikasi username. ID dibuat otomatis oleh database.
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Gagal terhubung ke database."}

    hashed_pw = hash_password(password)

    try:
        with conn.cursor() as cur:
            # 1. Cek duplikasi username
            cur.execute("SELECT username FROM users WHERE username = %s;", (username,))
            if cur.fetchone():
                return {"success": False, "message": "Username sudah terdaftar. Silakan gunakan yang lain."}

            # 2. Insert data ke tabel users (user_id dihilangkan agar auto-increment oleh Supabase)
            query = """
                INSERT INTO users (name, username, password_hash, role, is_active)
                VALUES (%s, %s, %s, %s, TRUE)
                RETURNING user_id, username, role;
            """
            cur.execute(query, (name, username, hashed_pw, role))
            new_user = cur.fetchone()
            conn.commit()

            return {
                "success": True,
                "message": "Registrasi berhasil.",
                "data": {"user_id": new_user[0], "username": new_user[1], "role": new_user[2]}
            }
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"Terjadi kesalahan sistem: {str(e)}"}
    finally:
        conn.close()

def login_user(username: str, password: str) -> dict:
    """
    Memvalidasi login pengguna.
    Mengecek kecocokan password dan status is_active (blokir/suspend).
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Gagal terhubung ke database."}

    try:
        with conn.cursor() as cur:
            # Tarik data user berdasarkan username
            query = """
                SELECT user_id, name, username, password_hash, role, is_active, avatar_path
                FROM users WHERE username = %s;
            """
            cur.execute(query, (username,))
            user = cur.fetchone()

            if not user:
                return {"success": False, "message": "Username tidak ditemukan."}

            # Mapping hasil query (karena berupa tuple)
            (user_id, name, db_username, password_hash, role, is_active, avatar_path) = user

            # Cek apakah akun sedang di-suspend oleh Admin
            if not is_active:
                return {"success": False, "message": "Akun ditangguhkan. Silakan hubungi Admin."}

            # Verifikasi kriptografi kata sandi
            if verify_password(password, password_hash):
                return {
                    "success": True,
                    "message": "Login berhasil.",
                    "data": {
                        "user_id": user_id,
                        "name": name,
                        "username": db_username,
                        "role": role,
                        "avatar_path": avatar_path
                    }
                }
            else:
                return {"success": False, "message": "Kata sandi salah."}
    except Exception as e:
        return {"success": False, "message": f"Terjadi kesalahan sistem: {str(e)}"}
    finally:
        conn.close()

def update_user_avatar(user_id: int, file_path: str) -> bool:
    """Memperbarui path foto profil pengguna di database."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            query = "UPDATE users SET avatar_path = %s WHERE user_id = %s;"
            cur.execute(query, (file_path, user_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error update_avatar: {e}")
        return False
    finally:
        conn.close()

def update_user_name(user_id: int, new_name: str) -> bool:
    """Memperbarui nama tampilan pengguna di tabel users."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            query = "UPDATE users SET name = %s WHERE user_id = %s;"
            cur.execute(query, (new_name, user_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error update_user_name: {e}")
        return False
    finally:
        conn.close()

def get_user_by_id(user_id: int) -> dict:
    """Mengambil data pengguna berdasarkan ID untuk auto-login via cookie."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            query = "SELECT user_id, name, username, role, avatar_path FROM users WHERE user_id = %s;"
            cur.execute(query, (user_id,))
            user = cur.fetchone()
            if user:
                return {
                    "user_id": user[0], 
                    "name": user[1], 
                    "username": user[2], 
                    "role": user[3], 
                    "avatar_path": user[4]
                }
            return None
    except Exception as e:
        print(f"Error get_user_by_id: {e}")
        return None
    finally:
        conn.close()

def update_user_password(user_id: int, old_password: str, new_password: str) -> dict:
    """Memperbarui kata sandi dengan verifikasi keamanan sandi lama."""
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Gagal terhubung ke database."}
    
    try:
        with conn.cursor() as cur:
            # Tarik password_hash saat ini
            cur.execute("SELECT password_hash FROM users WHERE user_id = %s;", (user_id,))
            user = cur.fetchone()
            
            if not user:
                return {"success": False, "message": "Akun tidak ditemukan."}
            
            current_hash = user[0]
            
            # Verifikasi password lama
            if not verify_password(old_password, current_hash):
                return {"success": False, "message": "Kata sandi lama salah."}
            
            # Hash password baru dan simpan (Gunakan format snake_case sesuai standar DB kamu)
            new_hashed_pw = hash_password(new_password)
            cur.execute("UPDATE users SET password_hash = %s WHERE user_id = %s;", (new_hashed_pw, user_id))
            conn.commit()
            
            return {"success": True, "message": "Kata sandi berhasil diperbarui!"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"Terjadi kesalahan sistem: {str(e)}"}
    finally:
        conn.close()

def cek_password_kuat(password):
    if len(password) < 8:
        return False, "Password minimal 8 karakter."
    if not re.search(r"[a-z]", password):
        return False, "Password harus mengandung minimal 1 huruf kecil."
    if not re.search(r"[A-Z]", password):
        return False, "Password harus mengandung minimal 1 huruf besar."
    if not re.search(r"\d", password):
        return False, "Password harus mengandung minimal 1 angka."
    if not re.search(r"[@$!%*?&#]", password):
        return False, "Password harus mengandung minimal 1 simbol khusus (@, $, !, %, dll)."
    return True, "Kuat"

# ==========================================
# BLOK PENGUJIAN (UNIT TESTING) DI TERMINAL
# ==========================================
if __name__ == "__main__":
    print("--- MULAI TES MODUL AUTH ---")

    # 1. Tes Registrasi Akun Baru
    print("\n[1] Tes Registrasi:")
    tes_daftar = register_user("Putra Parlindungan", "putra_pi", "rahasia123")
    print(tes_daftar)

    # 2. Tes Login dengan Password Benar
    print("\n[2] Tes Login (Valid):")
    tes_login_benar = login_user("putra_pi", "rahasia123")
    print(tes_login_benar)

    # 3. Tes Login dengan Password Salah
    print("\n[3] Tes Login (Password Salah):")
    tes_login_salah = login_user("putra_pi", "sandi_asal")
    print(tes_login_salah)