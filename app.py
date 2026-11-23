"""TunasMatch — demonstrasi klasifikasi tanaman, bukan resep budidaya."""
from __future__ import annotations

import csv
import html
import io

import pandas as pd
import streamlit as st

from crop_core import APP_NAME, CROP_NAMES, DISPLAY, FEATURES, ROOT, SOURCE_URL, load_bundle, predict_frame, range_warnings, read_json

st.set_page_config(page_title=APP_NAME, page_icon="🌱", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>{(ROOT / 'assets/theme.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def sprout_svg():
    """Ilustrasi dekoratif lokal; tidak bergantung CDN atau gambar eksternal."""
    return '''<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ilustrasi tunas tanaman">
    <ellipse cx="80" cy="140" rx="53" ry="9" fill="#cce1ce"/>
    <path d="M78 127V79c0-13 8-25 21-34" fill="none" stroke="#e4f2c2" stroke-width="8" stroke-linecap="round"/>
    <path d="M78 99C45 103 25 85 25 55c32-4 57 12 53 44Z" fill="#a8d48c"/>
    <path d="M80 76c-2-32 20-52 56-49 2 34-22 55-56 49Z" fill="#d6edaa"/>
    <path d="m43 73 34 25m25-42L82 76" stroke="#659e65" stroke-width="3" fill="none" stroke-linecap="round"/>
    <path d="M46 118h67l-9 24H56Z" fill="#d8a46c"/><path d="M43 115h73v10H43Z" fill="#edc092"/>
    </svg>'''


st.markdown(f'''<div class="app-brandbar">
<div class="brand-icon">{sprout_svg()}</div>
<div class="brand-copy"><div class="brand-name">{html.escape(APP_NAME)}</div>
<div class="brand-subtitle">Rekomendasi tanaman berdasarkan kondisi tanah dan iklim</div></div>
<div class="brand-badge">CROP RECOMMENDATION</div></div>''', unsafe_allow_html=True)


@st.cache_resource
def artifacts(version):
    return load_bundle(), read_json(ROOT / "results/summary.json")


try:
    bundle, summary = artifacts((ROOT / "results/summary.json").stat().st_mtime_ns)
except (OSError, ValueError) as exc:
    st.error(f"Artefak belum siap: {exc}. Jalankan python train.py dari folder proyek.")
    st.stop()

with st.sidebar:
    page = st.radio("Menu aplikasi", ["Rekomendasi", "Panduan", "Evaluasi model", "Kenali dataset"])
    st.divider()
    st.markdown('''<div class="sidebar-label">LANGKAH PENGGUNA</div>
    <div class="sidebar-step"><span>1</span><div><strong>Isi kondisi lahan</strong><small>Masukkan tujuh parameter yang sesuai</small></div></div>
    <div class="sidebar-step"><span>2</span><div><strong>Lihat rekomendasi</strong><small>Jalankan model yang sudah dilatih</small></div></div>
    <div class="sidebar-step"><span>3</span><div><strong>Jelajahi hasil</strong><small>Baca tanaman, skor, dan profil data</small></div></div>''', unsafe_allow_html=True)
    st.markdown(f'<div class="sidebar-model"><div class="sidebar-label">MODEL AKTIF</div><strong>{html.escape(bundle["selected_model"])}</strong><p>7 parameter · 22 tanaman</p></div>', unsafe_allow_html=True)
    st.caption("Dipilih melalui nested cross-validation pada training. Prototipe edukasi, bukan pengganti saran ahli pertanian.")


def show_image(filename, caption):
    st.image(str(ROOT / "plots" / filename), caption=caption, width="stretch")


examples = pd.read_csv(ROOT / "examples/contoh_dengan_label.csv").set_index("label")


def set_example(label="rice"):
    for f in FEATURES:
        st.session_state[f"input_{f}"] = float(examples.loc[label, f])
    st.session_state.pop("single_result", None)


if not all(f"input_{f}" in st.session_state for f in FEATURES):
    set_example()

if page == "Rekomendasi":
    st.title("Tanaman apa yang sesuai dengan lahanmu?")
    st.caption(f"{APP_NAME}: klasifikasi rekomendasi tanaman berdasarkan kandungan hara tanah dan kondisi iklim.")
    st.write("Masukkan tujuh kondisi lahan, lalu jelajahi rekomendasi tanamannya.")
    st.markdown(f'''<div class="hero"><div class="hero-copy">
        <h2>Dari tujuh petunjuk, jelajahi 22 tanaman.</h2>
        <p>Kenali pola hara tanah dan iklim melalui Crop Recommendation Dataset.</p>
        <div class="hero-tags"><span class="tag">2.200 data sumber</span><span class="tag">22 jenis tanaman</span><span class="tag">7 parameter lahan</span></div>
        </div><div class="hero-illustration">{sprout_svg()}</div></div>''', unsafe_allow_html=True)
    single, batch = st.tabs(["Satu lahan", "Banyak lahan / CSV"])
    with single:
        input_column, result_column = st.columns([1, 1], gap="large")
        with input_column, st.container(border=True, key="measurement_card"):
            st.markdown('<div class="smallcaps">01 / INPUT KONDISI LAHAN</div>', unsafe_allow_html=True)
            st.subheader("Kenali kondisi lahanmu")
            st.caption("Pilih contoh training untuk mencoba aplikasi, bukan untuk menguji akurasi.")
            example = st.selectbox("Pilih contoh tanaman", list(CROP_NAMES), format_func=lambda c: CROP_NAMES[c], index=list(CROP_NAMES).index("rice"))
            st.button("Muat contoh", on_click=set_example, args=(example,), width="stretch")
            st.markdown("#### Kandungan hara tanah")
            cols = st.columns(3)
            values = {}
            for col, f in zip(cols, FEATURES[:3]):
                with col:
                    values[f] = st.number_input(DISPLAY[f][0], min_value=0., step=1., key=f"input_{f}", help="Gunakan skala dataset; bukan dosis pupuk, persen NPK kemasan, atau konversi otomatis sensor.")
            st.markdown("#### Tanah dan iklim")
            cols = st.columns(2)
            for i, f in enumerate(FEATURES[3:]):
                limits = {"humidity": (0., 100.), "ph": (0., 14.), "rainfall": (0., None), "temperature": (-273.15, None)}[f]
                with cols[i % 2]:
                    values[f] = st.number_input(f"{DISPLAY[f][0]} ({'mm' if f == 'rainfall' else DISPLAY[f][1]})", min_value=limits[0], max_value=limits[1], step=.1, format="%.3f", key=f"input_{f}")
            st.caption("N/P/K: angka kandungan/rasio pada skala sumber; jangan dianggap dosis pupuk. Periode akumulasi hujan tidak tersedia di CSV. Untuk lahan nyata, pastikan definisinya cocok dahulu.")
            clicked = st.button("Lihat rekomendasi", type="primary", width="stretch")
            st.button("Reset contoh padi", on_click=set_example, width="stretch")
            signature = tuple(values[f] for f in FEATURES)
            if clicked:
                try:
                    x = pd.DataFrame([values], columns=FEATURES)
                    result, scores = predict_frame(x, bundle)
                    st.session_state.single_result = (signature, result, scores)
                except ValueError as exc: st.error(str(exc))
        with result_column, st.container(border=True, key="result_card"):
            st.markdown('<div class="smallcaps">02 / HASIL REKOMENDASI</div>', unsafe_allow_html=True)
            st.subheader("Pilihan tanamanmu")
            saved = st.session_state.get("single_result")
            if saved and saved[0] != signature:
                st.info("Input berubah. Klik Lihat rekomendasi untuk menghitung hasil terbaru.")
            elif saved:
                _, result, scores = saved
                row = result.iloc[0]
                label = row.rekomendasi
                st.markdown("### Hasil rekomendasi")
                score = float(scores.iloc[0][label])
                st.markdown(f'<div class="result-card">{sprout_svg()}<div><div class="eyebrow">REKOMENDASI UTAMA</div><h2>{CROP_NAMES[label]}</h2><p>Label sumber: {label}</p><strong>{score:.1%}</strong><p>skor model untuk kelas ini</p></div></div>', unsafe_allow_html=True)
                top = scores.iloc[0].sort_values(ascending=False, kind="stable").head(3)
                st.markdown("**Tiga skor kelas teratas**")
                # Tiga batang HTML lokal tidak membutuhkan unduhan renderer grafik.
                bars = "".join(f'<div class="score-label">{CROP_NAMES[c]} <b>{float(v):.2%}</b></div><div class="score-track"><div class="score-fill" style="width:{float(v)*100:.4f}%"></div></div>' for c,v in top.items())
                st.markdown(f'<div class="score-chart">{bars}</div>', unsafe_allow_html=True)
                st.caption("Urutan skor seri tidak menunjukkan perbedaan kecocokan. Pilihan tambahan berskor 0 bukan rekomendasi kuat.")
                st.warning("Skor bukan peluang sukses panen. Probabilitas belum dikalibrasi dan hanya membandingkan 22 kelas yang dikenal model.")
                warnings = range_warnings(result[FEATURES], bundle["bounds"])
                if warnings: st.warning("Di luar rentang training: " + ", ".join(warnings) + ". Model tetap menebak, tetapi hasilnya kurang dapat diandalkan; input di dalam rentang pun belum tentu representatif.")
                st.markdown(f"#### Seperti apa contoh {CROP_NAMES[label]} di data training?")
                profile = bundle["profiles"][label]
                profile_table = pd.DataFrame([{"Parameter": DISPLAY[f][0], "Input kamu": round(values[f], 2), "Minimum": round(profile[f]["min"], 2), "Median": round(profile[f]["median"], 2), "Maksimum": round(profile[f]["max"], 2)} for f in FEATURES])
                st.markdown('<div class="profile-table">' + profile_table.to_html(index=False, escape=True, border=0) + '</div>', unsafe_allow_html=True)
                st.caption("Ini ringkasan contoh berlabel tanaman tersebut. Bukan kondisi ideal agronomis, resep pemupukan, atau bukti hasil panen.")
                st.download_button("Unduh hasil CSV", result.to_csv(index=False).encode("utf-8"), "rekomendasi_tanaman.csv", "text/csv", width="stretch")
            else:
                st.markdown(f'<div class="result-card empty-result">{sprout_svg()}<div><h2>Siap mencocokkan</h2><p>Kenali kondisi lahan, jelajahi pilihan tanaman.</p></div></div>', unsafe_allow_html=True)
                st.info("Belum ada prediksi. Isi angka lalu klik Lihat rekomendasi.")
                st.markdown('''<div class="result-guide"><strong>Apa yang akan kamu dapatkan?</strong><p>Tanaman yang direkomendasikan, tiga skor kelas teratas, serta ringkasan kondisi tanaman di data training.</p><span>🌿 22 tanaman &nbsp; · &nbsp; 📊 Skor model &nbsp; · &nbsp; ↓ Unduh CSV</span></div>''', unsafe_allow_html=True)
    with batch:
        st.subheader("Prediksi beberapa lahan sekaligus")
        st.write("Unggah CSV dengan tujuh kolom wajib. Gunakan koma sebagai pemisah dan titik sebagai desimal. Tidak perlu kolom label.")
        a, b = st.columns(2)
        a.download_button("Unduh template kosong", (ROOT / "examples/template_input.csv").read_bytes(), "template_input.csv", "text/csv")
        b.download_button("Unduh 22 contoh training", (ROOT / "examples/contoh_batch.csv").read_bytes(), "contoh_batch.csv", "text/csv")
        upload = st.file_uploader("Upload CSV", type=["csv"], max_upload_size=5)
        if upload is not None:
            try:
                text = upload.getvalue().decode("utf-8-sig")
                header = next(csv.reader(io.StringIO(text)))
                if len(set(header)) != len(header): raise ValueError("Nama kolom CSV tidak boleh berulang.")
                data = pd.read_csv(io.StringIO(text))
                st.dataframe(data.head(10), hide_index=True, width="stretch")
                if st.button("Proses CSV", type="primary"):
                    out, _ = predict_frame(data, bundle)
                    st.success(f"Selesai memprediksi {len(out)} baris.")
                    extras = [c for c in data.columns if c not in FEATURES]
                    if extras: st.info("Kolom tambahan diabaikan: " + ", ".join(extras))
                    warnings = range_warnings(out[FEATURES], bundle["bounds"])
                    if warnings: st.warning("Ada input di luar rentang training: " + ", ".join(warnings))
                    st.dataframe(out, hide_index=True, width="stretch")
                    st.download_button("Unduh hasil batch", out.to_csv(index=False).encode("utf-8"), "hasil_batch.csv", "text/csv")
                    st.caption("Skor belum dikalibrasi. Data input tidak disimpan permanen oleh kode aplikasi.")
            except (ValueError, UnicodeError, StopIteration, pd.errors.ParserError) as exc:
                st.error(f"CSV tidak dapat diproses: {exc}")
elif page == "Evaluasi model":
    st.title("Evaluasi model")
    st.write("Angka di halaman ini berasal dari eksperimen yang benar-benar dijalankan, bukan angka contoh.")
    cols = st.columns(3)
    cols[0].metric("Model aktif", "Logistic Reg." if summary["selected_model"] == "Logistic Regression" else summary["selected_model"])
    cols[1].metric("Nested CV macro-F1", f"{summary['selected_cv']['cv_f1_macro_mean']:.2%}")
    cols[2].metric("Test accuracy", f"{summary['selected_test']['accuracy']:.2%}")
    tabs = st.tabs(["Perbandingan", "Kesalahan prediksi", "Fitur & pohon", "Pengaruh scaling"])
    with tabs[0]:
        st.markdown("#### Validasi untuk memilih model")
        st.dataframe(pd.read_csv(ROOT / "results/cv_comparison.csv"), hide_index=True, width="stretch")
        st.caption("Outer 5-fold menguji proses tuning inner 3-fold. SD antarfold bukan confidence interval. Fold saling berbagi training; selisih kecil belum membuktikan keunggulan signifikan.")
        show_image("perbandingan_cv.png", "Pemenang dipilih sebelum evaluasi test.")
        st.markdown("#### Ujian akhir: 440 contoh, 20 per tanaman")
        st.dataframe(pd.read_csv(ROOT / "results/test_comparison.csv"), hide_index=True, width="stretch")
        show_image("train_cv_test.png", "Bandingkan skor metrik yang sama; gap hanya indikasi, bukan diagnosis mutlak.")
        with st.expander("Parameter hasil tuning"):
            st.json(read_json(ROOT / "results/tuning.json"))
    with tabs[1]:
        model = st.selectbox("Lihat kesalahan model", ["KNN", "Decision Tree", "Logistic Regression"], index=["KNN", "Decision Tree", "Logistic Regression"].index(summary["selected_model"]))
        show_image(f"confusion_{model.replace(' ', '_')}.png", "Baris = tanaman sebenarnya; kolom = prediksi.")
        pairs = pd.read_csv(ROOT / "results/confused_pairs.csv")
        st.dataframe(pairs[pairs.model == model], hide_index=True, width="stretch")
        errors = pd.read_csv(ROOT / "results/test_errors.csv")
        with st.expander("Periksa tujuh angka pada contoh yang salah"):
            st.dataframe(errors[errors.model == model], hide_index=True, width="stretch")
        report = read_json(ROOT / "results/classification_reports.json")[model]
        st.dataframe(pd.DataFrame({k:v for k,v in report.items() if isinstance(v, dict)}).T, width="stretch")
        st.caption("Kemiripan kondisi adalah penjelasan yang perlu diperiksa pada data training; bukan bukti pasti penyebab suatu kesalahan.")
    with tabs[2]:
        show_image("feature_importance.png", "Impurity importance kandidat Decision Tree, bukan otomatis penjelasan lokal model aktif.")
        show_image("pohon_ringkas.png", "Hanya tingkat atas; pohon lengkap bisa lebih dalam.")
        st.download_button("Unduh aturan pohon lengkap", (ROOT / "results/aturan_decision_tree.txt").read_bytes(), "aturan_decision_tree.txt")
    with tabs[3]:
        show_image("scaling.png", "KNN k=5 dan DT max_depth=8 ditetapkan sama untuk kedua perlakuan.")
        st.dataframe(pd.read_csv(ROOT / "results/scaling_experiment.csv"), hide_index=True)
        st.caption("Scaling mengubah pembobotan jarak; tidak harus meningkatkan skor setiap dataset. DT tidak membutuhkannya karena urutan nilai dipertahankan.")
elif page == "Kenali dataset":
    st.title("Kenali dataset")
    st.write("2.200 contoh kondisi tanah dan iklim, tujuh fitur numerik, satu label tanaman, 22 kelas yang masing-masing berisi 100 contoh.")
    st.markdown(f"Sumber yang dirujuk: [Atharva Ingle — Crop Recommendation Dataset]({SOURCE_URL}). CSV lokal berasal dari berkas yang disediakan pengguna.")
    st.dataframe(pd.DataFrame([{"Kolom": f, "Arti": DISPLAY[f][0], "Satuan/catatan": DISPLAY[f][1]} for f in FEATURES]), hide_index=True, width="stretch")
    st.warning("NPK bukan dosis pupuk. Periode curah hujan dan detail satuan NPK perlu dikonfirmasi. Setiap baris adalah contoh berlabel; CSV tidak membuktikan 2.200 lahan berbeda atau kondisi optimal panen.")
    eda_tabs = st.tabs(["Kelas", "Distribusi", "Outlier", "Korelasi & kemiripan"])
    with eda_tabs[0]:
        show_image("distribusi_kelas.png", "Sumber seimbang; tidak menggunakan SMOTE atau class weighting.")
        st.write("Tidak ditemukan missing value maupun duplikat baris. Nilai ini diperiksa dari CSV lokal, bukan asumsi.")
    with eda_tabs[1]:
        show_image("histogram.png", "Rentang fitur berbeda. Grafik fitur memakai training saja.")
    with eda_tabs[2]:
        show_image("boxplot.png", "IQR menandai nilai untuk ditinjau; tidak ada baris otomatis dibuang.")
        show_image("kalium_per_kelas.png", "Nilai K tinggi berkelompok pada kelas tertentu dalam sumber; tidak otomatis salah pengukuran.")
    with eda_tabs[3]:
        show_image("korelasi.png", "Korelasi bukan sebab-akibat.")
        show_image("scatter_kemiripan.png", "Dua proyeksi fitur hanya membantu melihat pola; model memakai tujuh fitur.")
    st.download_button("Unduh dataset sumber", (ROOT / "Crop_recommendation.csv").read_bytes(), "Crop_recommendation.csv", "text/csv")
else:
    st.title("Panduan")
    st.markdown("""### Cara paling gampang
1. Buka **Rekomendasi**, pilih contoh, lalu **Muat contoh**.
2. Periksa tujuh angka. Untuk data sungguhan, gunakan pengukuran dengan definisi yang sesuai dataset.
3. Klik **Lihat rekomendasi**. Perhatikan tanaman utama, skor tiga kelas, dan peringatannya.
4. Untuk banyak baris, gunakan tab **Banyak lahan / CSV** dan template yang disediakan.

### Bahasa gampangnya
Komputer belajar menghubungkan tujuh petunjuk dengan nama tanaman yang sudah ada di tabel. Ia tidak menanam tanaman, tidak menguji hasil panen, dan tidak mengetahui harga pasar. Label adalah jawaban dataset, bukan jaminan bahwa hanya satu tanaman bisa tumbuh di lahan tersebut.

### Batas yang harus dipahami
- Data dirujuk dalam konteks India; belum divalidasi pada pengukuran lahan Indonesia.
- Literatur sumber menyebut augmentasi data; komposisi dan proses augmentasi CSV ini tidak dapat diaudit hanya dari tabelnya.
- Tidak ada fitur harga, hama, varietas, irigasi, tekstur tanah, lokasi, atau waktu.
- Skor model belum dikalibrasi. Input aneh tetap bisa mendapat skor tinggi.
- Ringkasan min/median/max bukan panduan kondisi ideal atau dosis pemupukan.
- Saat digunakan online, input dikirim ke server aplikasi. Kode tidak menulis input ke penyimpanan permanen.
""")
    st.caption("Aplikasi memakai model lokal tepercaya. Jangan memuat file joblib dari sumber asing. Tidak ada unggahan model pada antarmuka.")

st.divider()
st.caption(f"{APP_NAME} • Proyek pembelajaran mesin • Rekomendasi berbasis pola data, bukan jaminan keberhasilan budidaya.")
