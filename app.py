from datetime import datetime
import sqlite3
import pandas as pd
import streamlit as st

# Inisialisasi Database SQLite
def init_db():
    conn = sqlite3.connect("ticketing_spbe.db")
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            tanggal TEXT,
            pemohon TEXT,
            unit_kerja TEXT,
            jenis_layanan TEXT,
            keterangan TEXT,
            status_tugas TEXT,
            delegasi TEXT,
            status_penyelesaian TEXT
        )
    """
    )
    conn.commit()
    conn.close()

init_db()

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Portal SPBE - Diskominfo Babel",
    page_icon="🏛️",
    layout="wide",
)

# Sidebar Navigasi
st.sidebar.title("SPBE • DISKOMINFO")
menu = st.sidebar.selectbox(
    "Navigasi",
    [
        "Dashboard",
        "Pengajuan Layanan (OPD)",
        "Manajemen Petugas & Delegasi",
        "Laporan & Analisis",
    ],
)

# ---------------------------------------------------------
# 1. HALAMAN DASHBOARD
# ---------------------------------------------------------
if menu == "Dashboard":
    st.title("Dashboard Monitoring Layanan TIK")
    st.markdown(
        "Sistem Pengelolaan Layanan Jaringan Intra, Komunikasi, Pusat Data & Aplikasi berbasis ITIL 4."
    )

    conn = sqlite3.connect("ticketing_spbe.db")
    df = pd.read_sql("SELECT * FROM tickets", conn)
    conn.close()

    total_pekerjaan = len(df)
    baru = len(df[df["status_tugas"] == "Baru"]) if not df.empty else 0
    dikerjakan = (
        len(df[df["status_tugas"] == "Dikerjakan"]) if not df.empty else 0
    )
    selesai = len(df[df["status_tugas"] == "Selesai"]) if not df.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Pekerjaan", total_pekerjaan)
    col2.metric("Tiket Baru", baru)
    col3.metric("Sedang Dikerjakan", dikerjakan)
    col4.metric("Selesai", selesai)

    st.subheader("Daftar Pengajuan Terbaru")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info(
            "Belum ada data pengajuan tiket. Silakan buat pengajuan melalui menu Pengajuan Layanan."
        )

# ---------------------------------------------------------
# 2. HALAMAN PENGAJUAN LAYANAN (OPD)
# ---------------------------------------------------------
elif menu == "Pengajuan Layanan (OPD)":
    st.title("Formulir Pengajuan Layanan TIK")
    st.markdown(
        "Sesuai standar Katalog Layanan Diskominfo Provinsi Kepulauan Bangka Belitung."
    )

    with st.form("form_layanan"):
        nama_pemohon = st.text_input(
            "Nama Pemohon (Minimal Eselon III)"
        )
        unit_kerja = st.text_input("Nama Perangkat Daerah (OPD)")
        jenis_layanan = st.selectbox(
            "Pilih Jenis Layanan",
            [
                "Jaringan Intra Pemda",
                "Sistem Komunikasi Intra (Email/Zoom)",
                "Pusat Data (Colocation/Hosting)",
                "Pembangunan Aplikasi",
                "Sistem Penghubung (API/GSB)",
                "Manajemen Data (Satu Data)",
            ],
        )
        keterangan = st.text_area("Deskripsi Kebutuhan / Permasalahan")

        submitted = st.form_submit_button("Kirim Permohonan")
        if submitted:
            if nama_pemohon and unit_kerja and keterangan:
                ticket_id = (
                    f"SC04-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                )
                tanggal = datetime.now().strftime("%d %b %Y")
                status_tugas = "Baru"
                delegasi = "Belum didelegasikan"
                status_penyelesaian = "Open"

                conn = sqlite3.connect("ticketing_spbe.db")
                c = conn.cursor()
                c.execute(
                    "INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        ticket_id,
                        tanggal,
                        nama_pemohon,
                        unit_kerja,
                        jenis_layanan,
                        keterangan,
                        status_tugas,
                        delegasi,
                        status_penyelesaian,
                    ),
                )
                conn.commit()
                conn.close()

                st.success(
                    f"Permohonan berhasil dikirim! ID Tiket Anda: **{ticket_id}**"
                )
            else:
                st.error("Mohon lengkapi seluruh field sebelum mengirim.")

# ---------------------------------------------------------
# 3. MANAJEMEN PETUGAS & DELEGASI (SURAT TUGAS)
# ---------------------------------------------------------
elif menu == "Manajemen Petugas & Delegasi":
    st.title("Manajemen Delegasi & Penerbitan Surat Tugas Otomatis")
    st.markdown(
        "Alur SOP: Kadis -> Kabid e-Gov -> Ketua Tim -> Petugas Service Desk."
    )

    conn = sqlite3.connect("ticketing_spbe.db")
    df = pd.read_sql("SELECT * FROM tickets", conn)

    if not df.empty:
        ticket_ids = df["ticket_id"].tolist()
        selected_ticket = st.selectbox("Pilih ID Tiket untuk Didelegasikan", ticket_ids)

        ticket_data = df[df["ticket_id"] == selected_ticket].iloc[0]

        st.write(f"**Pemohon:** {ticket_data['pemohon']} ({ticket_data['unit_kerja']})")
        st.write(f"**Layanan:** {ticket_data['jenis_layanan']}")
        st.write(f"**Keterangan:** {ticket_data['keterangan']}")

        teknisi = st.multiselect(
            "Tunjuk Petugas / Teknisi (Penerbitan Surat Tugas Digital)",
            ["Erie Prayuda", "Ovi Novian", "Rahmat", "Tim Infrastruktur TIK"],
        )

        status_baru = st.selectbox(
            "Ubah Status Tugas", ["Baru", "Dikerjakan", "Selesai"]
        )

        if st.button("Simpan & Terbitkan Surat Tugas"):
            delegasi_str = (
                f"Didelegasikan kepada: {', '.join(teknisi)}"
                if teknisi
                else "Belum didelegasikan"
            )
            c = conn.cursor()
            c.execute(
                "UPDATE tickets SET status_tugas = ?, delegasi = ? WHERE ticket_id = ?",
                (status_baru, delegasi_str, selected_ticket),
            )
            conn.commit()
            conn.close()
            st.success("Surat Tugas dan status tiket berhasil diperbarui!")
            st.rerun()
    else:
        st.info("Belum ada tiket masuk.")

    conn.close()

# ---------------------------------------------------------
# 4. LAPORAN & ANALISIS
# ---------------------------------------------------------
elif menu == "Laporan & Analisis":
    st.title("Laporan Kinerja & Metrik SLA")
    st.markdown(
        "Analisis data operasional e-ticket untuk mendukung pengambilan keputusan berbasis data (Data-Driven Government)."
    )

    conn = sqlite3.connect("ticketing_spbe.db")
    df = pd.read_sql("SELECT * FROM tickets", conn)
    conn.close()

    if not df.empty:
        st.subheader("Rekapitulasi Berdasarkan Jenis Layanan")
        layanan_count = df["jenis_layanan"].value_counts()
        st.bar_chart(layanan_count)

        st.subheader("Tabel Log Transaksi Keseluruhan")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Belum ada data untuk ditampilkan dalam laporan.")