import bcrypt
import uuid
from database import get_db_connection

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