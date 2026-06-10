import time
import pandas as pd
import streamlit as st
from components import sidebar_profil
from backend.admin_ops import get_all_users, toggle_user_status, delete_user_permanently, get_system_stats, get_missing_foods_log

# 1. PROTEKSI HALAMAN (WAJIB ADA)
if not st.session_state.get("logged_in") or st.session_state.get("role") != "admin":
    st.error("🚫 Akses Ditolak: Halaman ini eksklusif untuk Admin.")
    st.stop()

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    sidebar_profil()

# ==========================================
# UI DASHBOARD UTAMA
# ==========================================
st.title("🛡️ Dashboard Admin")
st.divider()

@st.dialog("⚠️ Peringatan Fatal")
def dialog_hapus_user_admin(user_id, username, nama_lengkap):
    st.error(f"Apakah Anda yakin ingin memusnahkan akun **{nama_lengkap} (@{username})** beserta seluruh datanya? Tindakan ini tidak bisa dibatalkan.")
    
    col_y, col_n = st.columns(2)
    with col_y:
        if st.button("Ya, Musnahkan", type="primary", width="stretch"):
            if delete_user_permanently(user_id):
                st.toast(f"Akun @{username} berhasil dihapus permanen!", icon="🗑️")
                import time
                time.sleep(1.5)
                st.rerun()
    with col_n:
        if st.button("Batal", width="stretch"):
            st.rerun()

# 2. Papan Indikator
stats = get_system_stats()
col1, col2, col3 = st.columns(3)

col1.metric("👥 Total Pengguna", stats["total_users"])
col2.metric("💬 Total Sesi Obrolan", stats["total_sessions"])
col3.metric("⚠️ Makanan Gagal Dilacak", stats["total_missing"])

st.divider()

# 3. AREA NAVIGASI UTAMA
tab1, tab2 = st.tabs(["👥 Mengelola Pengguna", "⚠️ Makanan Gagal Dilacak"])

with tab1:
    st.subheader("👥 Mengelola Pengguna")
    users_data = get_all_users()
    
    if users_data:
        df_users = pd.DataFrame(users_data)
        
        # 1. SATU KOLOM PENCARIAN UNTUK SEMUA (Filter & Aksi)
        search_query = st.text_input("🔍 Cari pengguna (Nama/Username) atau ketik ID/Username spesifik untuk aksi:", placeholder="Misal: putra atau 10")
        
        # 2. LOGIKA AKSI (Muncul hanya jika input cocok persis dengan ID atau Username)
        if search_query:
            user_target = next((u for u in users_data if str(u["ID"]) == search_query.strip() or u["Username"].lower() == search_query.strip().lower()), None)
            
            if user_target:
                st.success(f"✅ Pengguna dipilih: **{user_target['Nama']}** (@{user_target['Username']})")
                
                _, col_btn1, col_btn2, _ = st.columns([1, 1.5, 1.5, 1])
                with col_btn1:
                    status_label = "Unsuspend" if not user_target["Status Aktif"] else "Suspend"
                    if st.button(f"🟡 {status_label}", width="stretch"):
                        if toggle_user_status(user_target["ID"], user_target["Status Aktif"]):
                            st.toast(f"Status {user_target['Username']} berhasil diubah!")
                            time.sleep(1)
                            st.rerun()
                with col_btn2:
                    # Saat diklik, jangan langsung hapus, tapi panggil pop-up dialog
                    if st.button("🔴 Hapus Akun", type="primary", width="stretch"):
                        dialog_hapus_user_admin(user_target["ID"], user_target["Username"], user_target["Nama"])
                st.divider()

        # 3. LOGIKA FILTER TABEL (Tabel akan selalu tersaring sesuai ketikan)
        if search_query:
            mask = (df_users["ID"].astype(str).str.contains(search_query, case=False) | 
                    df_users["Nama"].str.contains(search_query, case=False) | 
                    df_users["Username"].str.contains(search_query, case=False))
            df_display = df_users[mask]
        else:
            df_display = df_users
            
        # Tampilkan tabel
        st.dataframe(df_display, width="stretch", height=400, hide_index=True)
    else:
        st.info("Belum ada pengguna.")

with tab2:
    st.subheader("⚠️ Evaluasi Makanan Gagal Dilacak")
    missing_logs = get_missing_foods_log()
    
    if missing_logs:
        df_missing = pd.DataFrame(missing_logs)
        search_m = st.text_input("🔍 Cari log makanan:", placeholder="Cari...", key="search_missing_log")
        
        df_m_filtered = df_missing[df_missing["Kata Kunci (Gagal)"].str.contains(search_m, case=False)] if search_m else df_missing
        st.dataframe(df_m_filtered, width="stretch", height=380, hide_index=True)
        
        st.divider()
        st.subheader("📈 Top 5 Makanan Sering Gagal")
        top_m = df_missing["Kata Kunci (Gagal)"].value_counts().reset_index()
        top_m.columns = ["Nama Makanan", "Jumlah Pemicu Estimasi"]
        st.dataframe(top_m.head(5), width="stretch", hide_index=True)
    else:
        st.success("🎉 Belum ada log makanan gagal.")