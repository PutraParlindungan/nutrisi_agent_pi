import time
import streamlit as st
from backend import auth 
from backend.auth import cek_password_kuat



# Paksa sembunyikan sidebar di halaman login
st.markdown("""<style>[data-testid="stSidebar"]{display:none}</style>""", unsafe_allow_html=True)

# ==========================================
# 1. BAGIAN HEADER & EDUKASI AWAM
# ==========================================
col_logo, col_judul = st.columns([1, 10], vertical_alignment="center")

with col_logo:
    # Menggunakan path logo kustom kita
    st.image("assets/favicon.png", width="stretch") 

with col_judul:
    st.title("NutriAgent: Asisten Nutrisi Pintar")

st.markdown("""
Selamat datang! **NutriAgent** hadir untuk membantumu melacak nutrisi harian tanpa perlu pusing memikirkan angka. 
Cukup ceritakan apa yang kamu makan, dan biarkan AI kami yang menghitung semuanya untukmu.
""")

st.divider()

st.markdown("#### ✨ Kenapa Menggunakan NutriAgent?")
col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    with st.container(border=True):
        st.markdown("**🗣️ Seperti Ngobrol Biasa**")
        st.markdown("Tidak perlu repot mencari di daftar menu yang panjang. Ketik saja seperti kamu nge-chat teman: *'Pagi ini sarapan nasi uduk pakai telur dadar.'*")

with col_info2:
    with st.container(border=True):
        st.markdown("**🧠 Pintar & Instan**")
        st.markdown("AI kami langsung mengenali makananmu dan menghitung total Kalori, Protein, Karbohidrat, serta Lemak dalam hitungan detik.")

with col_info3:
    with st.container(border=True):
        st.markdown("**📈 Pantau Bebas Ribet**")
        st.markdown("Semua riwayat makanmu tersimpan rapi. Sangat cocok untuk kamu yang ingin diet, menambah massa otot, atau sekadar hidup lebih sehat.")

st.divider()

# ==========================================
# 2. AREA FORM LOGIN & REGISTER
# ==========================================
st.warning("💡 Siap memulai perjalanan sehatmu? Silakan masuk atau buat akun baru di bawah ini.")

tab_login, tab_reg = st.tabs(["Login", "Register"])

with tab_login:
    with st.form("login_form"):
        user_in = st.text_input("Username")
        pass_in = st.text_input("Password", type="password")
        btn_login = st.form_submit_button("Masuk")

        if btn_login:
            res = auth.login_user(user_in, pass_in)
            if res["success"]:
                st.session_state.logged_in = True
                st.session_state.user_id = res["data"]["user_id"]
                st.session_state.name = res["data"]["name"]
                st.session_state.role = res["data"]["role"]
                st.session_state.username = res["data"]["username"]
                st.session_state.avatar_path = res["data"].get("avatar_path", "")
                st.session_state.just_logged_in = True
                
                # Cookie berlaku selama 7 hari
                st.session_state.cookie_manager.set('user_id', res["data"]["user_id"], max_age=604800)
                
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
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        confirm_pass = st.text_input("Konfirmasi Password", type="password")
        btn_reg = st.form_submit_button("Daftar Sekarang")

        if btn_reg:
            if not new_name or not new_user or not new_pass or not confirm_pass:
                st.warning("Data tidak boleh kosong!")
            elif new_pass != confirm_pass:
                st.warning("Konfirmasi Password tidak cocok!")
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