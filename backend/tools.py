import os
import base64
import requests
import warnings
from dotenv import load_dotenv
from langchain_core.tools import tool
from supabase import create_client, Client

warnings.filterwarnings("ignore")
load_dotenv()

# --- INISIALISASI SUPABASE ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("[WARNING] Kredensial Supabase tidak ditemukan di .env!")

# --- FUNGSI FATSECRET ---
def get_fatsecret_token():
    client_id = os.getenv("FATSECRET_CLIENT_ID")
    client_secret = os.getenv("FATSECRET_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return None

    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    url = "https://oauth.fatsecret.com/connect/token"
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

@tool
def cari_nutrisi_makanan(nama_makanan: str, nama_asli: str = "") -> str:
    """
    Alat utama untuk mencari gizi makanan.
    - nama_makanan: nama dalam bahasa Inggris (untuk FatSecret)
    - nama_asli: nama asli yang diketik pengguna dalam bahasa Indonesia (untuk database lokal)
    """
    # Mencegah bug tipe data dict dari langchain
    if isinstance(nama_makanan, dict):
        nama_makanan = str(list(nama_makanan.values())[0])
    
    # Bersihkan string dari kutip bawaan LLM dan spasi berlebih
    clean_nama_makanan = str(nama_makanan).replace("'", "").replace('"', '').strip()
    clean_nama_asli = str(nama_asli).replace("'", "").replace('"', '').strip()
    
    # Prioritas kata kunci untuk log
    kata_kunci_log = clean_nama_asli if clean_nama_asli else clean_nama_makanan
    print(f"\n[DEBUG] Memulai Pencarian 3-Tier untuk: '{kata_kunci_log}'")

    # ==========================================
    # LAYER 1: SUPABASE INTERNAL (DATABASE LOKAL)
    # ==========================================
    print("[DEBUG] Mengecek Layer 1 (Database Lokal / Supabase)...")
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            # Prioritaskan 'nama_asli' untuk pencarian lokal agar tidak terjadi translasi
            query_lokal = clean_nama_asli if clean_nama_asli else clean_nama_makanan
            
            if query_lokal:
                # Pencarian ilike (case-insensitive) di tabel nutrition_data
                db_response = supabase.table("nutrition_data").select("*").ilike("name", f"%{query_lokal}%").limit(3).execute()
                
                if db_response.data and len(db_response.data) > 0:
                    lokal = db_response.data[0] # Ambil hasil paling relevan
                    nama = lokal.get("name")
                    kalori = lokal.get("calories", 0)
                    lemak = lokal.get("fat", 0)
                    karbo = lokal.get("carbohydrate", 0)
                    protein = lokal.get("proteins", 0)
                    
                    print(f"[DEBUG] Ditemukan di Layer 1 (Supabase TKPI): {nama}")
                    return f"[SUMBER: DATABASE LOKAL] Data gizi untuk {nama}: Calories: {kalori}kcal | Fat: {lemak}g | Carbs: {karbo}g | Protein: {protein}g"
                else:
                    print(f"[DEBUG] Layer 1 tidak menemukan '{query_lokal}'.")
        except Exception as e:
            print(f"[DEBUG] Error Layer 1 (Supabase): {str(e)}")
    else:
        print("[DEBUG] Supabase tidak dikonfigurasi dengan benar.")

    # ==========================================
    # LAYER 2: FATSECRET API
    # ==========================================
    print("[DEBUG] Layer 1 Kosong. Beralih ke Layer 2 (FatSecret)...")
    token = get_fatsecret_token()
    if token:
        url = "https://platform.fatsecret.com/rest/server.api"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "method": "foods.search",
            "search_expression": clean_nama_makanan, # FatSecret menggunakan versi Inggris/umum
            "format": "json",
            "region": "ID",
            "max_results": 5
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                print(f"[DEBUG] Kueri Bersih FatSecret: '{clean_nama_makanan}'")
                
                food_data = data.get('foods', {}).get('food')
                if food_data:
                    # Normalisasi struktur jika JSON mengembalikan 1 objek (bukan list)
                    if not isinstance(food_data, list):
                        food_data = [food_data]

                    best_match = food_data[0]
                    print(f"[DEBUG] Ditemukan di Layer 2: {best_match['food_name']}")
                    
                    return (
                        f"[SUMBER: FATSECRET] Alat menemukan kandidat: '{best_match['food_name']}' "
                        f"dengan nutrisi: {best_match['food_description']}. "
                        f"PERINGATAN PENTING UNTUK AI: Evaluasi dengan logika Anda! Apakah '{best_match['food_name']}' "
                        f"benar-benar makanan yang sama/relevan dengan '{clean_nama_makanan}' atau '{clean_nama_asli}'? "
                        f"Jika TIDAK NYAMBUNG (contoh: user minta 'Krabby Patty' tapi alat memunculkan 'Potato Patty'), "
                        f"TOLAK data FatSecret ini! Anda WAJIB melakukan estimasi sendiri dan gunakan tag '(Sumber: Estimasi AI)'."
                    )
                else:
                    print(f"[DEBUG] Layer 2 (FatSecret) tidak menemukan '{clean_nama_makanan}'.")
            else:
                print(f"[DEBUG] API FatSecret Error: HTTP {response.status_code}")
        except Exception as e:
            print(f"[DEBUG] Error Sistem Layer 2: {str(e)}")

    # ==========================================
    # LAYER 3 TRIGGER: LLM ESTIMATION
    # ==========================================
    print("[DEBUG] Layer 1 & 2 Gagal. Memicu Layer 3 (Estimasi AI)...")
    return f"DATA_TIDAK_DITEMUKAN: '{clean_nama_makanan}' atau '{clean_nama_asli}' tidak ada di Database Lokal maupun FatSecret. INSTRUKSI UNTUK AI: Gunakan pengetahuan internal Anda (Layer 3) untuk memberikan estimasi gizi yang masuk akal, dan beritahu pengguna bahwa ini adalah '[Estimasi AI]'."

# Blok pengujian manual
if __name__ == "__main__":
    print(cari_nutrisi_makanan.invoke("nasi goreng"))