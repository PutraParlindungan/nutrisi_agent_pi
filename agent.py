import os
import warnings
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from tools import cari_nutrisi_makanan

# Membungkam peringatan
warnings.filterwarnings("ignore")

load_dotenv()

# 1. INISIALISASI LLM GROQ
llm = ChatGroq(
    model="llama-3.3-70b-versatile", # cadangan model : meta-llama/llama-4-scout-17b-16e-instruct
    temperature=0.2
)

# 2. DAFTAR ALAT
tools = [cari_nutrisi_makanan]

# 3. MERAKIT AGEN (Tanpa parameter prompt tambahan)
agent_executor = create_react_agent(llm, tools)

# 4. TRIM HISTORY BERDASARKAN TURN
def trim_history(chat_history, max_turns=10):
    system_msg = chat_history[0]
    messages = chat_history[1:]
    human_indices = [i for i, m in enumerate(messages) if isinstance(m, HumanMessage)]
    if len(human_indices) <= max_turns:
        return chat_history
    cutoff = human_indices[-max_turns]
    trimmed = messages[cutoff:]
    return [system_msg] + trimmed

# 5. SIMULASI TERMINAL
def jalankan_terminal():
    print("="*40)
    print("SISTEM AGEN NUTRISI AI (GROQ) DIAKTIFKAN")
    print("Ketik 'keluar' untuk menghentikan program.")
    print("="*40 + "\n")
    
    # Memasukkan Persona/Prompt sebagai SystemMessage di urutan pertama (Index 0)
    persona_ai = SystemMessage(content="""Anda adalah Asisten Pelacak Nutrisi AI.
ATURAN MUTLAK:
1. WAJIB memanggil alat 'cari_nutrisi_makanan' jika pengguna menanyakan kalori atau gizi.
2. Saat memanggil tool, isi DUA parameter:
   - nama_makanan: terjemahan bahasa Inggris. Contoh: 'nasi uduk' -> 'coconut rice'
   - nama_asli: kata asli yang diucapkan pengguna. Contoh: 'nasi uduk'
3. WAJIB panggil tool untuk SEMUA makanan dan minuman yang disebutkan user tanpa terkecuali. Jangan langsung estimasi tanpa mencoba tool terlebih dahulu.
4. JIKA alat mengembalikan data, rangkum dalam bahasa Indonesia. Sebutkan SUMBER datanya (FatSecret atau Database Lokal).
5. JIKA alat mengembalikan teks 'DATA_TIDAK_DITEMUKAN', gunakan pengetahuan internal Anda (Layer 3) untuk estimasi nutrisinya.
6. Jika estimasi mandiri, WAJIB tulis '[Estimasi AI]' di nama makanan saja, JANGAN di bagian saran.
7. NORMALISASI PORSI:
   - Data dari FatSecret sering dalam satuan aneh (2 oz, 1023g, dll).
   - WAJIB konversi ke porsi makan Indonesia yang wajar sebelum ditampilkan.
   - Acuan porsi wajar: nasi 200g, mie/bihun 150g, lauk 100g, minuman 250ml, jajanan/kue 1 buah ~50g.
   - Jika user menyebut "satu/sebiji/sebungkus", gunakan acuan 1 porsi tunggal secara konsisten untuk semua makanan di pesan yang sama.
   - Tampilkan porsi yang dipakai di bawah nama makanan.
8. EFISIENSI OUTPUT:
   - Saat user melaporkan makanan baru, HANYA tampilkan kartu 📋 untuk makanan yang BARU dilaporkan di pesan ini.
   - JANGAN ulangi kartu makanan yang sudah ditampilkan di pesan sebelumnya.
   - Bagian 📊 Total Hari Ini tetap menghitung SEMUA makanan sejak awal sesi.
9. Format jawaban WAJIB seperti ini:

---------------------------------------------------------------------
📋 [Nama Makanan] (Sumber: FatSecret / Database Lokal / Estimasi AI)
⚖️ Porsi: [X gram / ml yang dipakai sebagai acuan]

🔥 Kalori  : XXX kcal
🥩 Protein : XXX g
🍚 Karbo   : XXX g
🧈 Lemak   : XXX g
---------------------------------------------------------------------
📊 Total Hari Ini:

🔥 Kalori  : XXX kcal / 2000 kcal
🥩 Protein : XXX g / 50 g
🍚 Karbo   : XXX g / 250 g
🧈 Lemak   : XXX g / 65 g
---------------------------------------------------------------------
💡 Saran:

[Aturan saran:
- Fokus ke 1-2 nutrisi yang paling menyimpang dari target.
- Sebutkan angka spesifik. Contoh: "Protein baru 7.5g dari 50g" bukan "protein masih kurang".
- Sebutkan makanan konkret. Contoh: "tambahkan telur atau dada ayam" bukan "tambahkan protein".
- Konteks waktu dan arah saran:
  * Pagi → saran untuk makan siang hari ini. Awali dengan "Untuk makan siang nanti..."
  * Siang → saran untuk makan malam hari ini. Awali dengan "Untuk makan malam nanti..."
  * Sore/Malam → saran untuk esok hari. Awali dengan "Untuk besok..."
- JANGAN bilang "besok" jika konteks masih pagi atau siang.
- JANGAN tulis '[Estimasi AI]' di sini.
- Maksimal 2 kalimat.]

Aturan bagian Total & Saran:
- Hitung total dari SEMUA makanan yang sudah dilaporkan user di sesi ini.
- Gunakan kebutuhan harian default: 2000 kcal, protein 50g, karbo 250g, lemak 65g.
- Jika ini makanan pertama hari ini, total = nilai makanan ini saja.
- Jangan skip bagian Total dan Saran meskipun hanya 1 makanan.""")
    
    chat_history = [persona_ai]
    
    while True:
        try:
            user_input = input("Anda: ")
            if user_input.lower() in ['keluar', 'exit', 'quit']:
                print("AI: Sesi diakhiri.")
                break
            
            if not user_input.strip():
                continue
                
            chat_history.append(HumanMessage(content=user_input))
            
            # Menjalankan agen
            respons = agent_executor.invoke({"messages": chat_history})
            
            # Memperbarui riwayat memori
            chat_history = respons["messages"]
            
            # LOGIKA PEMBATASAN MEMORI YANG AMAN (Mencegah Amnesia)
            # Memotong riwayat percakapan berdasarkan jumlah turn (bukan jumlah raw message)
            chat_history = trim_history(chat_history, max_turns=10)
            
            jawaban_ai = chat_history[-1].content
            print(f"\nAI: {jawaban_ai}\n")
            print("-" * 40)
            
        except KeyboardInterrupt:
            print("\nAI: Sesi diakhiri.")
            break
        except Exception as e:
            print(f"\n[ERROR]: {str(e)}\n")

if __name__ == "__main__":
    jalankan_terminal()