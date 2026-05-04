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

# --- FUNGSI FATSECRET (LAYER 1) ---
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
    if isinstance(nama_makanan, dict):
        nama_makanan = str(list(nama_makanan.values())[0])
    
    nama_makanan = str(nama_makanan).strip()
    kata_kunci = nama_makanan.lower().split()
    
    print(f"\n[DEBUG] Memulai Pencarian 3-Tier untuk: '{nama_makanan}'")

    # ==========================================
    # LAYER 1: FATSECRET API
    # ==========================================
    token = get_fatsecret_token()
    if token:
        # [UBAHAN BARU]: Bersihkan string dari kutip dan spasi berlebih bawaan AI
        clean_nama = nama_makanan.replace("'", "").replace('"', '').strip()
        
        url = "https://platform.fatsecret.com/rest/server.api"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "method": "foods.search",
            "search_expression": clean_nama,
            "format": "json",
            "region": "ID",
            "max_results": 5
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                
                # [TAMBAHAN DEBUG]: Intip kueri bersih dan respons mentah API
                print(f"[DEBUG] Kueri Bersih: '{clean_nama}'")
                print(f"[DEBUG] RAW JSON: {data}")
                
                food_data = data.get('foods', {}).get('food')
                
                if food_data:
                    if not isinstance(food_data, list):
                        food_data = [food_data]

                    best_match = food_data[0]
                    print(f"[DEBUG] Ditemukan di Layer 1: {best_match['food_name']}")
                    return f"[SUMBER: FATSECRET] Data gizi untuk {best_match['food_name']}: {best_match['food_description']}"
                else:
                    print(f"[DEBUG] FatSecret tidak menemukan '{clean_nama}'")
            else:
                print(f"[DEBUG] API FatSecret Error: HTTP {response.status_code}")
        except Exception as e:
            print(f"[DEBUG] Error Sistem Layer 1: {str(e)}")

    # ==========================================
    # LAYER 2: SUPABASE INTERNAL (KAGGLE/TKPI)
    # ==========================================
    print("[DEBUG] Layer 1 Gagal. Beralih ke Layer 2 (Supabase)...")
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            # Mencari menggunakan ilike (case-insensitive) pada kolom 'name'
            # Menggunakan .ilike agar "Nasi Goreng" tetap cocok dengan "Nasi"
            query_lokal = nama_asli if nama_asli.strip() else nama_makanan
            db_response = supabase.table("nutrition_data").select("*").ilike("name", f"%{query_lokal}%").limit(3).execute()
            
            if db_response.data and len(db_response.data) > 0:
                # Ambil hasil yang paling relevan (index 0)
                lokal = db_response.data[0]
                nama = lokal.get("name")
                kalori = lokal.get("calories", 0)
                lemak = lokal.get("fat", 0)
                karbo = lokal.get("carbohydrate", 0)
                protein = lokal.get("proteins", 0)
                
                print("[DEBUG] Ditemukan di Layer 2 (Supabase TKPI)")
                return f"[SUMBER: DATABASE LOKAL] Data gizi untuk {nama}: Calories: {kalori}kcal | Fat: {lemak}g | Carbs: {karbo}g | Protein: {protein}g"
        except Exception as e:
            print(f"[DEBUG] Error Layer 2 (Supabase): {str(e)}")

    # ==========================================
    # LAYER 3 TRIGGER: LLM ESTIMATION
    # ==========================================
    print("[DEBUG] Layer 1 & 2 Gagal. Memicu Layer 3 (Estimasi AI)...")
    return f"DATA_TIDAK_DITEMUKAN: '{nama_makanan}' tidak ada di FatSecret maupun Supabase. INSTRUKSI UNTUK AI: Gunakan pengetahuan internal Anda (Layer 3) untuk memberikan estimasi gizi yang masuk akal, dan beritahu pengguna bahwa ini adalah '[Estimasi AI]'."

# Blok pengujian manual
if __name__ == "__main__":
    print(cari_nutrisi_makanan.invoke("nasi goreng"))