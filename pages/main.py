import re
import time
import streamlit as st
from backend import auth 
from components import sidebar_profil, init_session 
from streamlit_cookies_controller import CookieController

cookie = init_session()

# ==========================================
# BLOKIR UI SELAMA LOADING COOKIE
# ==========================================
if st.session_state.get("is_checking_cookie"):
    # Tampilkan spinner saja, lalu hentikan eksekusi kode di bawahnya
    with st.spinner("Memuat sesi Anda..."):
        time.sleep(0.5) # Beri nafas sedikit agar UI tidak crash
    st.stop()

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

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

if st.session_state.logged_in:
    with st.sidebar:
        sidebar_profil() 

st.title("🥗 NutriAgent PI")
st.markdown("""
Selamat datang di **NutriAgent**! Asisten pelacak nutrisi cerdas Anda.

Sistem ini dibangun menggunakan ekosistem **LangGraph** dan model **Llama-3.3-70b-versatile** untuk melacak gizi harian Anda dengan akurasi tinggi.

#### 🛠️ Mengapa NutriAgent?
* **Pencarian Cerdas:** Terhubung langsung ke database makanan global dan Tabel Komposisi Pangan Indonesia (TKPI).
* **Sistem Anti-Gagal:** Jika makanan lokal tidak dikenali, AI akan memberikan estimasi otomatis.
* **Rekap Abadi:** Data gizi Anda aman tersimpan di database PostgreSQL.
""")

st.divider()

if not st.session_state.logged_in:
    # BLOKIR FORM LOGIN PADA PUTARAN PERTAMA
    if not st.session_state.logged_in:
        st.info("💡 Untuk menggunakan Agen AI di menu 'Agent Nutrisi', silakan masuk atau daftar terlebih dahulu.")

    tab_login, tab_reg = st.tabs(["Masuk", "Daftar Akun"])

    with tab_login:
        with st.form("login_form"):
            user_in = st.text_input("Username")
            pass_in = st.text_input("Password", type="password")
            btn_login = st.form_submit_button("Login")

            if btn_login:
                res = auth.login_user(user_in, pass_in)
                if res["success"]:
                    st.session_state.logged_in = True
                    st.session_state.user_id = res["data"]["user_id"]
                    st.session_state.name = res["data"]["name"]
                    st.session_state.role = res["data"]["role"]
                    st.session_state.username = res["data"]["username"]
                    st.session_state.avatar_path = res["data"].get("avatar_path", "")
                    
                    # ==========================================
                    # 4. TANAM COOKIE SAAT LOGIN BERHASIL
                    # ==========================================
                    # Cookie berlaku selama 7 hari (7 * 86400 detik)
                    cookie.set('user_id', res["data"]["user_id"], max_age=604800)
                    
                    st.success(f"Selamat datang, {res['data']['name']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(res["message"])

    with tab_reg:
        if "reg_success" in st.session_state:
            st.success(st.session_state.reg_success)
            del st.session_state.reg_success 

        with st.form(f"reg_form_{st.session_state.reg_form_key}", clear_on_submit=False):
            new_name = st.text_input("Nama Lengkap")
            new_user = st.text_input("Username Baru")
            new_pass = st.text_input("Password Baru", type="password")
            confirm_pass = st.text_input("Konfirmasi Password", type="password")
            btn_reg = st.form_submit_button("Daftar Sekarang")

            if btn_reg:
                if not new_name or not new_user:
                    st.warning("Data tidak boleh kosong!")
                elif new_pass != confirm_pass:
                    st.warning("Password tidak cocok!")
                else:
                    is_strong, msg_strength = cek_password_kuat(new_pass)
                    
                    if not is_strong:
                        st.error(f"⚠️ Pendaftaran Gagal: {msg_strength}")
                    else:
                        reg_res = auth.register_user(new_name, new_user, new_pass)
                        if reg_res["success"]:
                            st.session_state.reg_success = "✅ Akun berhasil dibuat! Silakan klik tab 'Masuk' di atas untuk login."
                            st.session_state.reg_form_key += 1
                            st.rerun()
                        else:
                            st.error(reg_res["message"])

else:
    st.success(f"Halo, **{st.session_state.name}**! Anda sudah masuk ke dalam sistem.")
    st.markdown("👉 **Silakan buka menu `Agent Nutrisi` di *sidebar* sebelah kiri untuk mulai mengobrol dengan Agen AI.**")