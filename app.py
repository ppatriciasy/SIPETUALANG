import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from io import BytesIO
from datetime import datetime
from PIL import Image
import streamlit_authenticator as stauth
import base64
from csr_tracker_page import show_csr_tracker

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="SIPETUALANG",
    #  📑 SIPETUALANG | Sistem Informasi Pelaporan Terkini, Utama, dan Akurat di Lingkar Tambang 🌿
    page_icon="data/logo.png",
    layout="wide",
)


def load_users():
    try:
        return pd.read_csv("data/users.csv")
    except:
        st.error("❌ File users.csv tidak ditemukan!")
        return None


users = load_users()

# --- Path file ---
DATA_PATH = "data/data_penyakit.csv"
ANNOUNCE_PATH = "data/pengumuman.txt"
BANNER_PATH = "data/banner.jpg"


# Inisialisasi session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Jika belum login → tampilkan form login
if not st.session_state.logged_in:
    with st.sidebar:
        st.title("Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user_match = users[  # type: ignore
                (users["username"] == username) & (users["password"] == password)  # type: ignore
            ]

            if not user_match.empty:
                data = user_match.iloc[0]

                st.session_state.logged_in = True
                st.session_state.username = data["username"]
                st.session_state.nama = data["nama"]  # simpan nama
                st.session_state.kategori = data["kategori"]  # simpan kategori
                st.rerun()
            else:
                st.error("❌ Username atau password salah!")

    tab0, tab1, tab2, tab3, tab4 = st.tabs(
        [
            "SIPETUALANG",
            "📊 Dashboard Publik",
            "🩺 Cek Diagnosa Dini",
            "📚 Informasi & Edukasi Kesehatan",
            "🎮 Games Sanitary Camp",
        ]
    )

    with tab0:
        st.image("data/img-bgrn.png")
        st.markdown(
            f"""
        <div style='text-align:center; color:#888; font-size:13px; margin-top:0px;'>
            © 2025 <b>SIPETUALANG</b>. All rights reserved.
        </div>
        """,
            unsafe_allow_html=True,
        )

    with tab1:
        # ===========================================================
        # ================ DASHBOARD PUBLIK =========================
        # ===========================================================
        st.header("📊 Dashboard Publik")

        waktu_sekarang = datetime.now()
        tanggal_hari_ini = waktu_sekarang.strftime("%A, %d %B %Y")
        st.markdown(f"🗓️ **Tanggal hari ini:** {tanggal_hari_ini}")

        st.info(
            "Menampilkan data 10 penyakit terbesar berdasarkan laporan dari nakes dan masyarakat"
        )

        # --- 1️⃣ Penanda waktu update terakhir ---
        last_updated = datetime.fromtimestamp(os.path.getmtime(DATA_PATH))
        st.caption(
            f"📅 **Data terakhir diperbarui:** {last_updated.strftime('%d %B %Y, %H:%M:%S')}"
        )

        # ===========================================================
        # 🔎 FILTER DATA (Tahun, Bulan, Kelompok Umur)
        # ===========================================================
        DIAGNOSA_PATH = "data/diagnosa_masyarakat.csv"
        DATA_NAKES_PATH = "data/data_pasien_nakes.csv"

        df_diagnosa = (
            pd.read_csv(DIAGNOSA_PATH)
            if os.path.exists(DIAGNOSA_PATH)
            else pd.DataFrame()
        )
        df_nakes = (
            pd.read_csv(DATA_NAKES_PATH)
            if os.path.exists(DATA_NAKES_PATH)
            else pd.DataFrame()
        )

        # ======================================
        # ⏰ REAL TIME DEFAULT (Bulan & Tahun)
        # ======================================
        today = datetime.now()
        current_year = today.strftime("%Y")
        current_month = today.strftime("%m")

        # Gabungkan tahun dari kedua data
        tahun_list = sorted(
            list(
                set(
                    df_diagnosa["Tanggal"].str[:4].unique().tolist()
                    if "Tanggal" in df_diagnosa.columns
                    else []
                ).union(
                    set(
                        df_nakes["Tanggal Input"].str[:4].unique().tolist()
                        if "Tanggal Input" in df_nakes.columns
                        else []
                    )
                )
            )
        )

        bulan_list = [
            "",
            "01",
            "02",
            "03",
            "04",
            "05",
            "06",
            "07",
            "08",
            "09",
            "10",
            "11",
            "12",
        ]

        kategori_umur_list = [
            "",
            "Ibu Hamil",
            "Bayi/Balita (0–5 tahun)",
            "Anak-anak (6–11 tahun)",
            "Remaja (12–18 tahun)",
            "PUS/WUS (19–49 tahun)",
            "Lansia (50+ tahun)",
        ]

        st.markdown("### 🎛️ Filter Data")
        colF1, colF2, colF3 = st.columns(3)

        with colF1:
            tahun_filter = st.selectbox(
                "📅 Pilih Tahun",
                [""] + tahun_list,
                index=(
                    (tahun_list.index(current_year) + 1)
                    if current_year in tahun_list
                    else 0
                ),
            )

        with colF2:
            bulan_filter = st.selectbox(
                "🗓️ Pilih Bulan",
                bulan_list,
                index=(
                    bulan_list.index(current_month)
                    if current_month in bulan_list
                    else 0
                ),
            )

        with colF3:
            umur_filter = st.selectbox("🎂 Kelompok Umur", kategori_umur_list)

        # ======================
        # 🔍 Terapkan Filter
        # ======================
        def apply_filters(df, tanggal_col):
            if df.empty:
                return df

            df_filtered = df.copy()

            # Jika kosong maka gunakan real-time
            year_to_use = tahun_filter if tahun_filter != "" else current_year
            month_to_use = bulan_filter if bulan_filter != "" else current_month

            df_filtered = df_filtered[df_filtered[tanggal_col].str[:4] == year_to_use]
            df_filtered = df_filtered[df_filtered[tanggal_col].str[5:7] == month_to_use]

            if umur_filter:
                if "Umur" in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered["Umur"] == umur_filter]

            return df_filtered

        df_diagnosa_filtered = apply_filters(df_diagnosa, "Tanggal")
        df_nakes_filtered = apply_filters(df_nakes, "Tanggal Input")

        st.markdown("---")

        # ===========================================================
        # 🔍 10 Penyakit Berdasarkan Diagnosa Nakes
        # ===========================================================
        st.markdown("### 💉 10 Penyakit Berdasarkan Data Nakes (Terfilter)")

        if not df_nakes_filtered.empty:
            top10_nakes = (
                df_nakes_filtered["Diagnosa"].value_counts().head(10).reset_index()
            )
            top10_nakes.columns = ["Diagnosa", "Jumlah Kasus"]
            st.dataframe(top10_nakes, use_container_width=True)
        else:
            st.info("Tidak ada data dari nakes sesuai filter.")

        st.markdown("---")

        st.markdown("### 📊 Grafik 10 Penyakit Terbesar Berdasarkan Data Nakes")

        if not df_nakes_filtered.empty:
            col1, col2 = st.columns(2)

            # --- Bar Chart ---
            with col1:
                fig_bar, ax_bar = plt.subplots()
                ax_bar.bar(top10_nakes["Diagnosa"], top10_nakes["Jumlah Kasus"])
                plt.xticks(rotation=45, ha="right")
                ax_bar.set_title("Bar Chart")
                st.pyplot(fig_bar)

            # --- Pie Chart ---
            with col2:
                fig_pie, ax_pie = plt.subplots()
                ax_pie.pie(
                    top10_nakes["Jumlah Kasus"],
                    labels=top10_nakes["Diagnosa"],  # type: ignore
                    autopct="%1.1f%%",
                )
                ax_pie.set_title("Pie Chart")
                st.pyplot(fig_pie)

        # ===========================================================
        # 🔍 10 Penyakit Berdasarkan Diagnosa Masyarakat
        # ===========================================================
        st.markdown("### 🧑‍⚕️ 10 Penyakit Berdasarkan Diagnosa Masyarakat (Terfilter)")

        if not df_diagnosa_filtered.empty:
            top10_diagnosa = (
                df_diagnosa_filtered["Diagnosa"].value_counts().head(10).reset_index()
            )
            top10_diagnosa.columns = ["Diagnosa", "Jumlah Kasus"]
            st.dataframe(top10_diagnosa, use_container_width=True)
        else:
            st.info("Tidak ada data masyarakat sesuai filter.")

        st.markdown(
            "### 📊 Grafik 10 Penyakit Terbesar Berdasarkan Diagnosa Masyarakat"
        )

        if not df_diagnosa_filtered.empty:
            colA, colB = st.columns(2)

            # --- Bar Chart ---
            with colA:
                fig_bar2, ax_bar2 = plt.subplots()
                ax_bar2.bar(top10_diagnosa["Diagnosa"], top10_diagnosa["Jumlah Kasus"])
                plt.xticks(rotation=45, ha="right")
                ax_bar2.set_title("Bar Chart")
                st.pyplot(fig_bar2)

            # --- Pie Chart ---
            with colB:
                fig_pie2, ax_pie2 = plt.subplots()
                ax_pie2.pie(
                    top10_diagnosa["Jumlah Kasus"],
                    labels=top10_diagnosa["Diagnosa"],  # type: ignore
                    autopct="%1.1f%%",
                )
                ax_pie2.set_title("Pie Chart")
                st.pyplot(fig_pie2)

        # ===========================================================
        # 📝 FITUR KOMENTAR
        # ===========================================================

        st.markdown("## 🗨️ Tulis Komentar")

        komentar_path = "data/komentar_pengunjung.csv"
        os.makedirs("data", exist_ok=True)

        # --- Form Input Komentar ---
        with st.form("form_komentar"):
            nama_komen = st.text_input("👤 Nama Anda")
            waktu_komen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            komentar = st.text_area("💬 Komentar Anda (saran, kritik, masukan)")

            submit_komen = st.form_submit_button("✉️ Kirim Komentar")

        if submit_komen:
            if not nama_komen or not komentar:
                st.error("⚠️ Nama dan komentar tidak boleh kosong.")
            else:
                new_komen = pd.DataFrame(
                    [
                        {
                            "Nama": nama_komen,
                            "Komentar": komentar,
                            "Waktu": waktu_komen,
                        }
                    ]
                )

                if os.path.exists(komentar_path):
                    df_k_old = pd.read_csv(komentar_path)
                    df_k_all = pd.concat([df_k_old, new_komen], ignore_index=True)
                else:
                    df_k_all = new_komen

                df_k_all.to_csv(komentar_path, index=False)
                st.success("✅ Komentar berhasil dikirim!")

        # --- Tampilkan Komentar dalam Bentuk Bubble Chat ---
        st.markdown("### 💬 Komentar")

        if os.path.exists(komentar_path):
            df_k_show = pd.read_csv(komentar_path)

            if len(df_k_show) > 0:

                for idx, row in df_k_show.iterrows():
                    nama = row["Nama"]
                    isi = row["Komentar"]
                    waktu = row["Waktu"]

                    st.markdown(
                        f"""
                        <div style="
                            background-color:#dcf8c6;
                            padding:10px 15px;
                            margin-bottom:10px;
                            border-radius:15px;
                            max-width:100%;
                            box-shadow:0 2px 4px rgba(0,0,0,0.1);
                        ">
                            <strong style="color:#075e54;">{nama}</strong><br>
                            <span style="font-size:15px;">{isi}</span><br>
                            <span style="font-size:11px; color:#555; float:right;">{waktu}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            else:
                st.info("Belum ada komentar yang masuk.")
        else:
            st.info("Belum ada komentar pengunjung.")

    with tab2:
        # ===========================================================
        # ========== FITUR CEK DIAGNOSA DINI ========================
        # ===========================================================
        st.header("🩺 Cek Diagnosa Dini Berdasarkan Keluhan")

        st.markdown(
            """
        Isi form di bawah ini untuk mendapatkan perkiraan diagnosa awal berdasarkan keluhan Anda.  
        ⚠️ *Hasil ini bukan pengganti pemeriksaan medis, segera periksa ke fasilitas kesehatan terdekat untuk kepastian diagnosis.*
        """
        )

        # --- Form Input Data Masyarakat ---
        with st.form("form_diagnosa"):
            st.markdown(
                """
                <div style="text-align:center;">
                """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("📸 Scan Kartu Tanda Penduduk (KTP)")
                st.markdown(
                    "Scan KTP untuk isi data otomatis, atau isi formulir di bawah."
                )
                nama = st.text_input("👤 Nama Pasien")
                nik = st.text_input("🆔 NIK")
                usia = st.selectbox(
                    "🎂 Kelompok Umur",
                    [
                        "",
                        "Ibu Hamil",
                        "Bayi/Balita (0–5 tahun)",
                        "Anak-anak (6–11 tahun)",
                        "Remaja (12–18 tahun)",
                        "PUS/WUS (19–49 tahun)",
                        "Lansia (50+ tahun)",
                    ],
                )

            with col2:
                jenis_kelamin = st.selectbox(
                    "🚻 Jenis Kelamin", ["Laki-laki", "Perempuan"]
                )
                alamat = st.text_area("🏠 Alamat")
                keluhan = st.text_area(
                    "💬 Keluhan Utama (contoh: batuk, pilek, tenggorokan sakit)"
                )

            # --- Tambahan: tombol & total data sejajar ---
            col1, col2 = st.columns([2, 1])

            with col1:
                submitted = st.form_submit_button("🔍 Cek Diagnosa")

            with col2:
                # Tampilkan total data diagnosa di samping tombol
                file_path = "data/diagnosa_masyarakat.csv"
                total_data = 0
                if os.path.exists(file_path):
                    df_total = pd.read_csv(file_path)
                    total_data = len(df_total)
                st.markdown(
                    f"""
                    <p style='text-align:right; color:#333; margin-top:8px;'>
                        Total data diagnosa: {total_data}
                    </p>
                    """,
                    unsafe_allow_html=True,
                )

        if submitted:
            if not nama or not nik or not keluhan:
                st.error(
                    "⚠️ Mohon isi minimal **Nama**, **NIK**, dan **Keluhan** untuk melanjutkan."
                )
            else:
                # --- Analisis Diagnosa Berdasarkan Kata Kunci ---
                keluhan_lower = keluhan.lower()
                if any(
                    k in keluhan_lower
                    for k in ["batuk", "pilek", "bersin", "tenggorokan", "flu"]
                ):
                    diagnosa = "ISPA (Infeksi Saluran Pernapasan Akut)"
                elif any(
                    k in keluhan_lower
                    for k in ["diare", "mual", "muntah", "perut", "pencernaan"]
                ):
                    diagnosa = "Gangguan Pencernaan"
                elif any(
                    k in keluhan_lower
                    for k in ["demam", "panas", "nyeri kepala", "meriang"]
                ):
                    diagnosa = "Demam / Infeksi Umum"
                elif any(
                    k in keluhan_lower
                    for k in ["pusing", "tekanan darah", "darah tinggi", "jantung"]
                ):
                    diagnosa = "Hipertensi"
                elif any(
                    k in keluhan_lower for k in ["gatal", "ruam", "bintik", "kulit"]
                ):
                    diagnosa = "Penyakit Kulit"
                else:
                    diagnosa = (
                        "Belum teridentifikasi (segera periksa ke fasilitas kesehatan)"
                    )

                # --- Tampilkan Hasil Diagnosa ---
                st.success(f"🩺 **Hasil Analisis:** {diagnosa}")
                st.info(
                    "💡 Segera lakukan pemeriksaan ke fasilitas kesehatan terdekat untuk memastikan diagnosa dan mendapatkan pengobatan yang tepat."
                )

                # --- Simpan ke CSV ---
                os.makedirs("data", exist_ok=True)
                file_path = "data/diagnosa_masyarakat.csv"
                tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                new_data = pd.DataFrame(
                    [
                        {
                            "Nama": nama,
                            "NIK": nik,
                            "Umur": usia,
                            "Jenis Kelamin": jenis_kelamin,
                            "Alamat": alamat,
                            "Keluhan": keluhan,
                            "Diagnosa": diagnosa,
                            "Tanggal": tanggal,
                        }
                    ]
                )

                if os.path.exists(file_path):
                    df_old = pd.read_csv(file_path)
                    df_all = pd.concat([df_old, new_data], ignore_index=True)
                else:
                    df_all = new_data

                df_all.to_csv(file_path, index=False)
                st.success(
                    "✅ Data berhasil disimpan dan akan dianalisis di Dashboard Admin."
                )

    with tab3:
        # ===========================================================
        # ============ Informasi & Edukasi Kesehatan ================
        # ===========================================================

        DATA_DIR = "data"  # folder tempat file disimpan
        BANNER_PATH = os.path.join(DATA_DIR, "banner.jpg")
        ANNOUNCE_PATH = os.path.join(DATA_DIR, "pengumuman.txt")

        # st.image("data/banner.jpg")

        # st.markdown(
        #     f"<div class='banner'>📢 <b>Pengumuman:</b> Posyandu Hari Minggu Di Balai Desa X</div>",
        #     unsafe_allow_html=True,
        # )

        # ============================================================
        # 1) INFORMASI
        # ============================================================
        st.subheader("📰 INFORMASI")

        # Pengumuman
        if os.path.exists(ANNOUNCE_PATH):
            pengumuman = open(ANNOUNCE_PATH, "r", encoding="utf-8").read().strip()
            if pengumuman:
                st.markdown(
                    """
                    <div style="
                        padding:15px;
                        border-radius:10px;
                        background:#FFF4D6;
                        border-left:10px solid #FFBB33;
                        margin-bottom:15px;">
                        <span style="font-size:20px;">📢</span> 
                        <b>Pengumuman:</b> """
                    + pengumuman
                    + """
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Banner
        if os.path.exists(BANNER_PATH):
            st.image(BANNER_PATH, use_container_width=True)
        else:
            st.info("📸 Belum ada banner. Unggah dari menu admin.")

        # ============================================================
        # 2) EDUKASI KESEHATAN (GRID + CARD)
        # ============================================================
        st.subheader("📘 EDUKASI KESEHATAN")

        def load_image_base64(path):
            with open(path, "rb") as img:
                return base64.b64encode(img.read()).decode()

        daftar_buku = [
            {
                "icon": "data/buku-profil.png",
                "judul": "Profil Kesehatan Masyarakat Lingkar Tambang",
                "deskripsi": "Profil Kesehatan Masyarakat Lingkar Tambang Kabupaten Lahat 2025.",
                "link": "https://heyzine.com/flip-book/f8c084b932.html",
            },
            {
                "icon": "data/buku-saku.png",
                "judul": "Masyarakat Sehat Lingkar Tambang",
                "deskripsi": "Panduan ringkas untuk masyarakat sekitar tambang.",
                "link": "https://heyzine.com/flip-book/e01487ccf7.html",
            },
            {
                "icon": "data/buku-anak.png",
                "judul": "Suara Kecilku Di Bumi Batu Bara",
                "deskripsi": "Buku ajar untuk anak-anak di lingkar tambang.",
                "link": "https://heyzine.com/flip-book/e2b1493dcd.html",
            },
        ]

        # Grid 2 kolom otomatis responsif
        cols = st.columns(3)

        for i, buku in enumerate(daftar_buku):

            # Convert icon ke base64
            try:
                icon_b64 = load_image_base64(buku["icon"])
                img_html = f'<img src="data:image/png;base64,{icon_b64}" style="width:140px; height:180px; border-radius:0px;">'
            except:
                img_html = "<div style='font-size:50px;'>📘</div>"

            with cols[i]:
                st.markdown(
                    f"""
                    <div style="
                        background:white;
                        border-radius:15px;
                        padding:15px;
                        margin-bottom:20px;
                        border:1px solid #E0E0E0;
                        box-shadow:0 2px 6px rgba(0,0,0,0.05);
                        text-align:center;
                        height: 400px;
                    ">
                        {img_html}
                        <h5 style="margin-top:10px;">{buku['judul']}</h5>
                        <p style="color:#555; font-size:12px; height:50px;">{buku['deskripsi']}</p>
                        <a href="{buku['link']}" target="_blank">
                            <button style="
                                background:#4A90E2;
                                color:white;
                                padding:6px 14px;
                                border:none;
                                border-radius:8px;
                                cursor:pointer;
                                font-size:15px;
                            ">🔗 Buka Buku</button>
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # ============================================================
        # 3) KORAN ONLINE (CARD STYLE)
        # ============================================================
        st.subheader("🗞️ KORAN SIPETUALANG")

        st.markdown(
            """
            <div style="
                background:#E3F2FD;
                padding:20px;
                border-radius:12px;
                border:1px solid #90CAF9;
            ">
                <span style="font-size:35px;">📰</span>
                <b>PT ABC Salurkan Bantuan untuk Masyarakat Lingkar Tambang</b>
                <p style="margin-top:10px;color:#333;">
                    Lahat — Sebagai perusahaan tambang yang beroperasi di wilayah lingkar tambang, PT ABC kembali menunjukkan komitmennya dalam meningkatkan kesejahteraan masyarakat sekitar. Melalui program tanggung jawab sosial perusahaan (CSR), PT ABC menyalurkan berbagai bentuk bantuan yang menyasar kebutuhan kesehatan, pendidikan, dan lingkungan.
                </p>
                <a href="#" style="
                    text-decoration:none;
                    color:#0D47A1;
                    font-weight:bold;
                ">Baca selengkapnya…</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tab4:  # pastikan ini sesuai urutan tabs yang kamu pakai
        st.header("🎮 Games Sanitary Camp")

        st.markdown(
            """
            <p style='color:#444; font-size:16px;'>
                Nikmati permainan edukasi interaktif yang dirancang untuk memberikan pengetahuan kesehatan 
                dengan cara yang menyenangkan. Klik pada gambar untuk mulai bermain!
            </p>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <style>
                .game-card {
                    background: #ffffff;
                    border-radius: 12px;
                    padding: 15px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    transition: 0.2s;
                }
                .game-card:hover {
                    transform: scale(1.02);
                    box-shadow: 0 6px 16px rgba(0,0,0,0.18);
                }
                .game-img {
                    border-radius: 10px;
                    width: 100%;
                    height: auto;
                    cursor: pointer;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        img_path = "data/game-preview.png"

        if os.path.exists(img_path):
            img_b64 = base64.b64encode(open(img_path, "rb").read()).decode()

            st.markdown(
                f"""
                <a href="https://sanitary-camp.berandadigital.net" target="_blank">
                    <div class="game-card">
                        <img src="data:image/png;base64,{img_b64}" class="game-img"/>
                    </div>
                </a>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.error("❌ Gambar preview game tidak ditemukan di folder data/")

    st.stop()

with st.sidebar:
    st.title(f"Login sebagai {st.session_state.kategori}")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()


# --- Gaya CSS ---
st.markdown(
    """
    <style>
        .title {
            text-align: center;
            color: #1E88E5;
            font-size: 32px;
            font-weight: bold;
        }
        .subtitle {
            text-align: center;
            color: #555;
            font-size: 18px;
        }
        .book-box {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            background-color: #f9f9f9;
        }
        .banner {
            background-color: #FFF8E1;
            border-left: 8px solid #FFC107;
            padding: 12px;
            margin-bottom: 20px;
            border-radius: 8px;
        }
    </style>
""",
    unsafe_allow_html=True,
)


def ensure_csv(filename, columns):
    if not os.path.exists(filename):
        pd.DataFrame(columns=columns).to_csv(filename, index=False)


ensure_csv(
    "data/laporan_nakes.csv",
    ["timestamp", "desa", "penyakit", "jumlah_kasus", "urgensi", "uraian", "status"],
)

ensure_csv(
    "data/log_pemerintah.csv", ["timestamp", "id_laporan", "feedback", "status_baru"]
)

ensure_csv("data/log_pt.csv", ["timestamp", "id_laporan", "feedback", "status_baru"])


# --- Path file ---
DATA_PATH = "data/data_penyakit.csv"
ANNOUNCE_PATH = "data/pengumuman.txt"
BANNER_PATH = "data/banner.jpg"

# --- Judul Aplikasi ---
st.markdown(
    '<p class="title"> 📑 SIPETUALANG | Sistem Informasi Pelaporan Terkini, Utama, dan Akurat di Lingkar Tambang 🌿</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="subtitle">Analisis 10 Penyakit Terbesar dan Edukasi Kesehatan Masyarakat</p>',
    unsafe_allow_html=True,
)

# === Batasi menu sesuai kategori user ===

kategori = st.session_state.kategori

if kategori in ["Developer"]:
    allowed_menu = [
        "Dashboard Nakes",
        "Dashboard Pemerintah",
        "Dashboard PT",
        "Dashboard Admin",
    ]

elif kategori == "Admin":
    allowed_menu = [
        "Dashboard Admin",
        "Kelola Pengguna",
        "Log Aktivitas",
    ]

elif kategori == "Nakes":
    allowed_menu = [
        "Dashboard Nakes",
        "Data Pasien",
        "Laporan Masalah Desa",
    ]

elif kategori == "PT":
    allowed_menu = [
        "Dashboard PT",
        "CSR Perusahaan",
    ]

elif kategori == "Pemerintah":
    allowed_menu = [
        "Dashboard Pemerintah",
    ]

else:
    allowed_menu = ["Dashboard Publik"]  # fallback kalau user aneh


menu = st.sidebar.radio("📂 Menu Navigasi", allowed_menu)

# ===========================================================
# ========== DASHBOARD ADMIN ================================
# ===========================================================
if menu == "Dashboard Admin":

    st.header("👩🏻‍⚕️ Dashboard Admin")
    st.warning("Halaman ini hanya untuk pengelola data.")

    # --- Upload Banner Gambar ---
    st.subheader("🖼️ Unggah Banner Gambar")
    uploaded_banner = st.file_uploader(
        "Pilih file banner (JPG/PNG)", type=["jpg", "jpeg", "png"]
    )
    if uploaded_banner:
        os.makedirs("data", exist_ok=True)
        image = Image.open(uploaded_banner)
        image.save(BANNER_PATH)
        st.success(
            "✅ Banner berhasil diperbarui! Coba buka Informaasi dan Edukasi Kesehatan untuk melihat hasilnya."
        )
        st.image(BANNER_PATH, caption="Banner Baru", use_container_width=True)

    st.markdown("---")

    # --- 📢 Fitur Pengumuman ---
    st.subheader("📢 Atur Pengumuman Desa")
    os.makedirs("data", exist_ok=True)

    current_announcement = ""
    if os.path.exists(ANNOUNCE_PATH):
        with open(ANNOUNCE_PATH, "r", encoding="utf-8") as f:
            current_announcement = f.read()

    new_announcement = st.text_area(
        "Tulis pengumuman (misal: Posyandu minggu depan di Balai Desa!)",
        value=current_announcement,
        height=100,
    )
    if st.button("💾 Simpan Pengumuman"):
        with open(ANNOUNCE_PATH, "w", encoding="utf-8") as f:
            f.write(new_announcement.strip())
        st.success("📢 Pengumuman berhasil disimpan! Akan tampil di Dashboard Publik.")

    st.markdown("---")

    # ===========================================================
    # ========== TAMBAHAN: DATA DIAGNOSA MASYARAKAT =============
    # ===========================================================
    st.subheader("🩺 Data Diagnosa Masyarakat")

    file_path_diagnosa = "data/diagnosa_masyarakat.csv"

    if os.path.exists(file_path_diagnosa):
        df_diagnosa = pd.read_csv(file_path_diagnosa)

        st.write(f"Total data diagnosa masyarakat: **{len(df_diagnosa)}**")
        st.dataframe(df_diagnosa, use_container_width=True)

        # Tombol Unduh Data Diagnosa
        buffer_d = BytesIO()
        df_diagnosa.to_excel(buffer_d, index=False, sheet_name="Data_Diagnosa")
        buffer_d.seek(0)
        st.download_button(
            label="📥 Unduh Data Diagnosa (Excel)",
            data=buffer_d,
            file_name="Data_Diagnosa_Masyarakat.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    else:
        st.info("⚠️ Belum ada data diagnosa masyarakat yang masuk.")

    # ===========================================================
    # ========== TAMBAHAN: DATA PASIEN NAKES ====================
    # ===========================================================
    st.markdown("---")
    st.subheader("💊 Data Pasien dari Tenaga Kesehatan (Nakes)")

    file_path_nakes = "data/data_pasien_nakes.csv"

    if os.path.exists(file_path_nakes):
        df_nakes = pd.read_csv(file_path_nakes)
        st.write(f"Total data pasien dari nakes: **{len(df_nakes)}**")
        st.dataframe(df_nakes, use_container_width=True)

        buffer_n = BytesIO()
        df_nakes.to_excel(buffer_n, index=False, sheet_name="Data_Pasien_Nakes")
        buffer_n.seek(0)
        st.download_button(
            label="📥 Unduh Data Pasien Nakes (Excel)",
            data=buffer_n,
            file_name="Data_Pasien_Oleh_Nakes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info("📭 Belum ada data dari Tenaga Kesehatan yang masuk.")

# ===========================================================
# ========== DASHBOARD NAKES ================================
# ===========================================================

elif menu == "Dashboard Nakes":
    st.header("💉 Dashboard Tenaga Kesehatan (Nakes)")
    st.info(
        "Halaman ini digunakan oleh tenaga kesehatan untuk mencatat data pasien berdasarkan pemeriksaan langsung."
    )


elif menu == "Data Pasien":
    tab1, tab2 = st.tabs(["🧾 Input Data Pasien", "📋 Tabel Data Pasien"])

    with tab1:
        file_path_nakes = "data/data_pasien_nakes.csv"
        # ===========================================================
        # ========== TAB 1: INPUT DATA PASIEN =======================
        # ===========================================================
        st.subheader("🧾 Form Input Data Pasien")
        st.info(
            "Halaman ini digunakan oleh tenaga kesehatan untuk mencatat data pasien."
        )

        with st.form("form_data_pasien_nakes"):
            col1, col2 = st.columns(2)

            with col1:
                nama = st.text_input("👤 Nama Pasien")
                nik = st.text_input("🆔 NIK")
                usia = st.selectbox(
                    "🎂 Kelompok Umur",
                    [
                        "",
                        "Ibu Hamil",
                        "Bayi/Balita (0–5 tahun)",
                        "Anak-anak (6–11 tahun)",
                        "Remaja (12–18 tahun)",
                        "PUS/WUS (19–49 tahun)",
                        "Lansia (50+ tahun)",
                    ],
                )
                jenis_kelamin = st.selectbox(
                    "🚻 Jenis Kelamin", ["Laki-laki", "Perempuan"]
                )

            with col2:
                alamat = st.text_area("🏠 Alamat Pasien")
                keluhan = st.text_area("💬 Keluhan Utama")
                diagnosa = st.text_input(
                    "🩺 Diagnosa Medis (misal: ISPA, Hipertensi, dll)"
                )

            submitted = st.form_submit_button("💾 Simpan Data Pasien")

        if submitted:
            if not nama or not nik or not diagnosa:
                st.error("⚠️ Mohon isi minimal **Nama**, **NIK**, dan **Diagnosa**.")
            else:
                tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_data = pd.DataFrame(
                    [
                        {
                            "Nama": nama,
                            "NIK": nik,
                            "Umur": usia,
                            "Jenis Kelamin": jenis_kelamin,
                            "Alamat": alamat,
                            "Keluhan": keluhan,
                            "Diagnosa": diagnosa,
                            "Tanggal Input": tanggal,
                        }
                    ]
                )

                if os.path.exists(file_path_nakes):
                    df_old = pd.read_csv(file_path_nakes)
                    df_all = pd.concat([df_old, new_data], ignore_index=True)
                else:
                    df_all = new_data

                df_all.to_csv(file_path_nakes, index=False)
                st.success("✅ Data pasien berhasil disimpan.")

                with st.expander("📋 Lihat Data yang Baru Dimasukkan"):
                    st.dataframe(new_data, use_container_width=True)

    with tab2:
        # --- Tabel Data Pasien ---
        st.subheader("📋 Data Pasien yang Sudah Tercatat")
        st.info("Halaman ini digunakan oleh tenaga kesehatan melihat data pasien.")

        if os.path.exists(file_path_nakes):
            df_nakes = pd.read_csv(file_path_nakes)
            st.dataframe(df_nakes, use_container_width=True)

            buffer_n = BytesIO()
            df_nakes.to_excel(buffer_n, index=False, sheet_name="Data_Pasien_Nakes")
            buffer_n.seek(0)
            st.download_button(
                label="📥 Unduh Data Pasien (Excel)",
                data=buffer_n,
                file_name="Data_Pasien_Nakes.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info("📭 Belum ada data pasien yang dimasukkan.")


elif menu == "Laporan Masalah Desa":
    # ===========================================================
    # ========== TAB 2: LAPORAN MASALAH DESA ====================
    # ===========================================================
    st.subheader("📢 Form Laporan Masalah Kesehatan Desa")
    st.info(
        "Halaman ini digunakan oleh tenaga kesehatan untuk melaporkan masalah kesehatan."
    )

    file_path_laporan = "data/laporan_nakes.csv"
    os.makedirs("data", exist_ok=True)

    # Buat file laporan jika belum ada
    if not os.path.exists(file_path_laporan):
        pd.DataFrame(
            columns=[
                "timestamp",
                "desa",
                "penyakit",
                "jumlah_kasus",
                "urgensi",
                "uraian",
                "status",
            ]
        ).to_csv(file_path_laporan, index=False)

    desa = st.text_input("🏘️ Nama Desa")
    penyakit = st.text_input("🦠 Penyakit yang Meningkat")
    jumlah = st.number_input("📌 Jumlah Kasus", min_value=0, step=1)
    urgensi = st.selectbox("⚠️ Tingkat Urgensi", ["Rendah", "Sedang", "Tinggi"])
    uraian = st.text_area("📝 Uraian Masalah")

    if st.button("📨 Kirim Laporan"):
        if desa and penyakit:
            df_lapor = pd.read_csv(file_path_laporan)

            new_row = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "desa": desa,
                "penyakit": penyakit,
                "jumlah_kasus": jumlah,
                "urgensi": urgensi,
                "uraian": uraian,
                "status": "Menunggu Pemerintah",
            }

            df_lapor = pd.concat([df_lapor, pd.DataFrame([new_row])], ignore_index=True)
            df_lapor.to_csv(file_path_laporan, index=False)

            st.success("✅ Laporan berhasil dikirim.")
        else:
            st.error("⚠️ Mohon isi minimal **Nama Desa** dan **Penyakit**.")

    # ---- Tampilkan laporan yang sudah ada ----
    st.markdown("### 📊 Laporan Masalah Desa")
    df_show = pd.read_csv(file_path_laporan)

    if df_show.empty:
        st.info("Belum ada laporan desa.")
    else:
        st.dataframe(df_show, use_container_width=True)

    df = pd.read_csv("data/laporan_nakes.csv")

    st.markdown("### 🗂️ Riwayat Tindakan Laporan")

    idx = st.selectbox("Pilih ID Laporan", df.index)

    log_pem = pd.read_csv("data/log_pemerintah.csv")
    log_pt = pd.read_csv("data/log_pt.csv")

    # Filter log berdasarkan laporan yang dipilih
    riwayat_pem = log_pem[log_pem["id_laporan"] == idx]
    riwayat_pt = log_pt[log_pt["id_laporan"] == idx]

    if riwayat_pem.empty and riwayat_pt.empty:
        st.info("Belum ada riwayat tindakan untuk laporan ini.")
    else:
        if not riwayat_pem.empty:
            st.markdown("#### 🏛️ Riwayat Tindakan")
            st.dataframe(riwayat_pem, use_container_width=True)

        if not riwayat_pt.empty:
            st.markdown("#### 🏢 Feedback dari PT")
            st.dataframe(riwayat_pt, use_container_width=True)
# ===========================================================
# =============== DASHBOARD PEMERINTAH ======================
# ===========================================================
elif menu == "Dashboard Pemerintah":
    st.title("Dashboard Pemerintah")

    df = pd.read_csv("data/laporan_nakes.csv")

    if df.empty:
        st.info("Belum ada laporan dari nakes.")
    else:
        st.dataframe(df)

        idx = st.selectbox("Pilih ID Laporan", df.index)

        feedback = st.text_area("Feedback / Tindakan Pemerintah")

        status_baru = st.selectbox(
            "Status Laporan", ["Diproses Pemerintah", "Diteruskan ke PT", "Selesai"]
        )

        if st.button("Kirim Feedback"):
            # simpan feedback
            log = pd.read_csv("data/log_pemerintah.csv")
            new_log = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "id_laporan": idx,
                "feedback": feedback,
                "status_baru": status_baru,
            }
            log = pd.concat([log, pd.DataFrame([new_log])], ignore_index=True)
            log.to_csv("data/log_pemerintah.csv", index=False)

            # update status laporan nakes
            df.loc[idx, "status"] = status_baru
            df.to_csv("data/laporan_nakes.csv", index=False)

            st.success("Tindakan pemerintah disimpan!")

        st.markdown("### 🗂️ Riwayat Tindakan Laporan")

        log_pem = pd.read_csv("data/log_pemerintah.csv")
        log_pt = pd.read_csv("data/log_pt.csv")

        # Filter log berdasarkan laporan yang dipilih
        riwayat_pem = log_pem[log_pem["id_laporan"] == idx]
        riwayat_pt = log_pt[log_pt["id_laporan"] == idx]

        if riwayat_pem.empty and riwayat_pt.empty:
            st.info("Belum ada riwayat tindakan untuk laporan ini.")
        else:
            if not riwayat_pem.empty:
                st.markdown("#### 🏛️ Riwayat Tindakan")
                st.dataframe(riwayat_pem, use_container_width=True)

            if not riwayat_pt.empty:
                st.markdown("#### 🏢 Feedback dari PT")
                st.dataframe(riwayat_pt, use_container_width=True)

# ===========================================================
# ==================== DASHBOARD PT =========================
# ===========================================================
elif menu == "Dashboard PT":
    st.title("Dashboard PT")

    df = pd.read_csv("data/laporan_nakes.csv")
    df_pt = df[df["status"] == "Diteruskan ke PT"]

    if df_pt.empty:
        st.info("Tidak ada laporan yang perlu ditindaklanjuti PT.")
    else:
        st.dataframe(df_pt)

        idx = st.selectbox("Pilih ID Laporan", df_pt.index)

        feedback = st.text_area("Feedback / Tindakan PT")

        status_baru = st.selectbox("Update Status", ["Diproses PT", "Selesai"])

        if st.button("Kirim Feedback PT"):
            log = pd.read_csv("data/log_pt.csv")
            new_log = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "id_laporan": idx,
                "feedback": feedback,
                "status_baru": status_baru,
            }
            log = pd.concat([log, pd.DataFrame([new_log])], ignore_index=True)
            log.to_csv("data/log_pt.csv", index=False)

            df.loc[idx, "status"] = status_baru
            df.to_csv("data/laporan_nakes.csv", index=False)

            st.success("Feedback PT disimpan!")

if menu == "Dashboard PT":
    st.markdown("## 🗂️ Riwayat Lengkap Tindakan PT")

    if os.path.exists("data/log_pt.csv"):
        log_pt = pd.read_csv("data/log_pt.csv")

        if log_pt.empty:
            st.info("Belum ada riwayat tindakan PT.")
        else:
            st.dataframe(log_pt, use_container_width=True)
    else:
        st.info("Riwayat PT belum dibuat.")

elif menu == "CSR Perusahaan":
    show_csr_tracker()
