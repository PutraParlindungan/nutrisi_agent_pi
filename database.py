import psycopg2
import os
from dotenv import load_dotenv

# 1. Mengaktifkan pembaca file rahasia (.env)
load_dotenv()

def get_db_connection():
    """Fungsi utama untuk membuat koneksi ke PostgreSQL Supabase."""
    try:
        # 2. Mengambil data dari .env dan menyambungkannya ke driver psycopg2
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        return conn
    except Exception as e:
        print(f"Gagal terhubung ke database: {e}")
        return None

# 3. Blok penguji (Hanya jalan jika file ini dirun langsung)
if __name__ == "__main__":
    print("Mencoba terhubung ke Supabase...")
    koneksi = get_db_connection()
    
    if koneksi:
        print("Status: Berhasil terhubung ke database!")
        koneksi.close()