import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt


def show_csr_tracker():

    # --- CONFIG ---
    st.set_page_config(page_title="CSR Tracker - SIPETUALANG", layout="wide")

    # contoh path asset yang tersedia di environment (sesuaikan jika perlu)
    UPLOADED_ASSET = "/mnt/data/A_flat-style_digital_illustration_graphic_introduc.png"

    # --- CSS GAYA HALAMAN ---
    st.markdown(
        """
        <style>
        /* Summary cards */
        .summary-row { display:flex; gap:20px; margin-bottom:20px; }
        .card {
            background: #fff;
            padding:16px;
            border-radius:10px;
            box-shadow: 0 6px 18px rgba(14,30,37,0.06);
            border: 1px solid rgba(0,0,0,0.04);
            flex:1;
            min-width:150px;
        }
        .card h3 { margin:0; font-size:22px; }
        .card p { margin:6px 0 0 0; color:#555; font-size:14px; }

        /* Timeline */
        .timeline { border-left: 3px solid #e0e0e0; margin-left:10px; padding-left:18px; }
        .timeline-item { margin-bottom:18px; }
        .badge { display:inline-block; padding:6px 10px; border-radius:8px; font-size:12px; color:#fff; }

        /* small helper */
        .muted { color:#666; font-size:13px; }

        /* responsive images in cards */
        .card-img { width:100%; height:140px; object-fit:cover; border-radius:8px; margin-bottom:10px; }

        /* button look link */
        .link-btn { color:#0D47A1; font-weight:600; text-decoration:none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- UTILITY: pastikan CSV ada (contoh struktur) ---
    os.makedirs("data", exist_ok=True)
    CSR_CSV = "data/csr_log.csv"
    if not os.path.exists(CSR_CSV):
        sample = pd.DataFrame(
            [
                {
                    "tanggal": "2025-10-01",
                    "perusahaan": "PT ABC",
                    "jenis": "Kesehatan",
                    "kegiatan": "Bakti kesehatan & pengobatan gratis",
                    "penerima": 120,
                    "status": "Selesai",
                    "catatan": "Kerjasama puskesmas setempat",
                },
                {
                    "tanggal": "2025-10-15",
                    "perusahaan": "PT XYZ",
                    "jenis": "Lingkungan",
                    "kegiatan": "Penanaman 300 bibit pohon",
                    "penerima": 0,
                    "status": "Selesai",
                    "catatan": "Masyarakat dilibatkan",
                },
                {
                    "tanggal": "2025-11-05",
                    "perusahaan": "PT DEF",
                    "jenis": "Pendidikan",
                    "kegiatan": "Donasi alat tulis & beasiswa kecil",
                    "penerima": 45,
                    "status": "Direncanakan",
                    "catatan": "Jadwal belum final",
                },
            ]
        )
        sample.to_csv(CSR_CSV, index=False)

    # baca data CSR
    df_csr = pd.read_csv(CSR_CSV, parse_dates=["tanggal"])

    # === HEADER ===
    st.markdown("# ⭐ CSR Tracker: Aktivitas Sosial Perusahaan")
    st.markdown(
        "Pantau riwayat, keaktifan, dan dampak program CSR dari PT di Lingkar Tambang."
    )

    # === FILTERS BAR ===
    with st.expander("🔎 Filter & Pilihan Tampilan", expanded=False):
        colf1, colf2, colf3, colf4 = st.columns([2, 2, 2, 1])
        perusahaan_filter = colf1.multiselect(
            "Perusahaan",
            options=sorted(df_csr["perusahaan"].unique().tolist()),
            default=sorted(df_csr["perusahaan"].unique().tolist()),
        )
        jenis_filter = colf2.multiselect(
            "Jenis Kegiatan",
            options=sorted(df_csr["jenis"].unique().tolist()),
            default=sorted(df_csr["jenis"].unique().tolist()),
        )
        periode = colf3.date_input(
            "Rentang Tanggal",
            value=(df_csr["tanggal"].min().date(), df_csr["tanggal"].max().date()),
        )
        agg_by = colf4.selectbox(
            "Grafik",
            ["Bar Per Perusahaan", "Progress (%) per PT", "Tren Bulanan"],
            index=0,
        )

    # apply filters
    start_date, end_date = pd.to_datetime(periode[0]), pd.to_datetime(periode[1])  # type: ignore
    df_view = df_csr[
        (df_csr["perusahaan"].isin(perusahaan_filter))
        & (df_csr["jenis"].isin(jenis_filter))
        & (df_csr["tanggal"] >= start_date)
        & (df_csr["tanggal"] <= end_date)
    ].copy()

    # === SUMMARY CARDS ===
    total_kegiatan = len(df_view)
    top_pt = (
        df_view["perusahaan"].value_counts().idxmax() if total_kegiatan > 0 else "-"
    )
    total_penerima = int(df_view["penerima"].sum())

    st.markdown(
        f"""
        <div class="summary-row">
            <div class="card">
                <h3>{total_kegiatan}</h3>
                <p>Total Kegiatan (terfilter)</p>
            </div>
            <div class="card">
                <h3>{top_pt}</h3>
                <p>PT Paling Aktif</p>
            </div>
            <div class="card">
                <h3>{total_penerima}</h3>
                <p>Total Penerima Manfaat</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # === GRAFIK BESIDE ===
    col1, col2 = st.columns([1, 1])

    # Grafik kiri: Bar per perusahaan
    with col1:
        st.subheader("Keaktifan Perusahaan")
        if df_view.empty:
            st.info("Tidak ada data sesuai filter.")
        else:
            cnt = df_view["perusahaan"].value_counts()
            fig, ax = plt.subplots(figsize=(5, 3))
            cnt.plot(kind="bar", ax=ax)
            ax.set_ylabel("Jumlah Kegiatan")
            ax.set_xlabel("")
            ax.set_title("Jumlah Kegiatan per PT")
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            st.pyplot(fig)

    # Grafik kanan: Progress (%) vs target (contoh)
    with col2:
        st.subheader("Progress Target Tahunan (simulasi)")
        # Buat target dummy per perusahaan (bisa disimpan di file lain)
        targets = {
            pt: 12 for pt in df_view["perusahaan"].unique()
        }  # target 12 kegiatan/tahun default
        progress_data = []
        for pt, t in targets.items():
            done = df_view[df_view["perusahaan"] == pt].shape[0]
            pct = int(min(100, (done / t) * 100)) if t > 0 else 0
            progress_data.append({"pt": pt, "done": done, "target": t, "pct": pct})

        if len(progress_data) == 0:
            st.info("Tidak ada perusahaan terpilih.")
        else:
            for p in progress_data:
                st.markdown(f"**{p['pt']}** — {p['done']}/{p['target']} kegiatan")
                st.progress(p["pct"] / 100.0)
                st.markdown(
                    f"<div class='muted'>{p['pct']}% dari target tahunan</div>",
                    unsafe_allow_html=True,
                )

    # === TIMELINE + DETAIL RIWAYAT ===
    st.markdown("---")
    st.subheader("Tabel Riwayat (Detail)")
    st.dataframe(df_view.reset_index(drop=True), use_container_width=True)
    # Download CSV filtered
    csv_buffer = BytesIO()
    df_view.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    st.download_button(
        "📥 Unduh Riwayat (CSV)",
        data=csv_buffer,
        file_name="csr_riwayat_filtered.csv",
        mime="text/csv",
    )

    # === OPTIONAL: Grafk tren bulanan bila dipilih ===
    if agg_by == "Tren Bulanan" and not df_view.empty:
        st.markdown("---")
        st.subheader("Tren Bulanan Kegiatan (Grafik)")
        df_view["bulan"] = df_view["tanggal"].dt.to_period("M").astype(str)
        trend = df_view.groupby(["bulan", "perusahaan"]).size().unstack(fill_value=0)
        fig2, ax2 = plt.subplots(figsize=(10, 3))
        trend.plot(ax=ax2)
        ax2.set_ylabel("Jumlah Kegiatan")
        ax2.set_xlabel("")
        ax2.grid(axis="y", linestyle="--", alpha=0.4)
        st.pyplot(fig2)

    # === FOOTER / INFO ===
    st.markdown("---")
    st.markdown(
        f"<div style='text-align:right; color:#888; font-size:12px;'>Terakhir diperbarui: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>",
        unsafe_allow_html=True,
    )

    # --- END ---
