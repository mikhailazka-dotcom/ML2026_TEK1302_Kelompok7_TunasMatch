"""Bangun PPT, satu Word, notebook, dan panduan dari angka eksperimen nyata.

Tidak training ulang. Untuk notebook yang ber-output: python execute_notebook.py.
"""
from __future__ import annotations

import importlib.metadata
import json
import math
import textwrap
from pathlib import Path

import nbformat as nbf
import pandas as pd
from docx import Document
from docx.shared import Cm, Pt as DPt, RGBColor as DColor
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

from crop_core import APP_NAME, CROP_NAMES, DISPLAY, FEATURES, ROOT, SOURCE_URL, TITLE, read_json
from build_ppt_template import build_ppt_from_template
from references import REFERENCES


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def mdtable(headers, rows):
    clean = lambda v: str(v).replace("|", "/").replace("\n", " ")
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"] + ["| " + " | ".join(map(clean, row)) + " |" for row in rows])


def tables(cv, test):
    merged = cv.merge(test, on="model")
    return mdtable(["Model", "Nested CV F1 ± SD", "Test accuracy", "Precision macro", "Recall macro", "F1 macro"],
        [[r.model, f"{r.cv_f1_macro_mean:.4f} ± {r.cv_f1_macro_std:.4f}", f"{r.accuracy:.4f}", f"{r.precision_macro:.4f}", f"{r.recall_macro:.4f}", f"{r.f1_macro:.4f}"] for r in merged.itertuples()])


def build_reference_docs():
    rows = []
    for r in REFERENCES:
        rows.append([r["id"], f"{r['authors']} ({r['year']})", r["problem"], r["dataset"], r["methods"], r["metrics"], r["result"], r["difference"], "https://doi.org/" + r["doi"]])
    headers = ["No", "Penulis & Tahun", "Permasalahan", "Dataset", "Metode/Algoritma", "Metrik Evaluasi", "Hasil Utama", "Perbedaan dengan Project", "DOI"]
    write(ROOT / "references/Tabel_Studi_Literatur.md", "# Tabel studi literatur — lima artikel jurnal\n\n" + mdtable(headers, rows) + "\n\nAngka jurnal adalah laporan penulis, bukan hasil replikasi kami. Perbedaan split, dataset, preprocessing dan metrik membuat ranking lintas artikel tidak setara. Tanggal akses: 10 November 2026. Konfirmasi kelayakan referensi kepada dosen; tidak ada klaim persetujuan.")
    pd.DataFrame(rows, columns=headers).to_csv(ROOT / "references/Tabel_Studi_Literatur.csv", index=False, encoding="utf-8-sig")
    entries = []
    for r in REFERENCES:
        entries.append(f"## [{r['id']}] {r['title']}\n\n{r['authors']} ({r['year']}). {r['journal']}. https://doi.org/{r['doi']}\n\nBaca: {r['url']}\n\nRingkasan: {r['result']}\n\nBukti yang dibaca: {r['evidence']}\n\nPerbedaan: {r['difference']}")
    write(ROOT / "references/Daftar_5_Jurnal.md", "# Daftar lima jurnal relevan\n\n" + "\n\n".join(entries) + "\n\nPDF hanya tersedia lokal jika unduhan berhasil; periksa verification_log.json. Tautan/DOI dan metadata tetap tersedia. Jangan menganggap halaman HTML error sebagai PDF. Tidak ada jurnal atau angka hasil yang dikarang.")


def make_sections(s, config, cv, test):
    best = s["selected_model"]
    weakest = cv.iloc[-1].model
    imp = pd.read_csv(ROOT / "results/feature_importance_dt.csv")
    pairs = pd.read_csv(ROOT / "results/confused_pairs.csv")
    bp = pairs[pairs.model == best]
    sc = pd.read_csv(ROOT / "results/scaling_experiment.csv")
    bounds = pd.read_csv(ROOT / "results/descriptive_source.csv", index_col=0)
    top_test = test.sort_values("f1_macro", ascending=False).iloc[0]
    rows = [[f, DISPLAY[f][0], DISPLAY[f][1], f"{bounds.loc[f, 'min']:.2f}–{bounds.loc[f, 'max']:.2f}"] for f in FEATURES]
    tasks = mdtable(["Nama", "NIM", "Tugas"], [[m["name"], m["nim"], m["task"]] for m in config["members"]])
    sections = [
        ("01_Penjelasan_Bahasa_Sederhana.md", f"""# 1. Sebenarnya kita sedang bikin apa?

Bayangin kamu punya buku latihan. Di setiap baris ada tujuh petunjuk kondisi tanah dan cuaca, lalu ada nama tanaman. Kita mengajari komputer membaca hubungan petunjuk dengan nama tanaman itu.

Kalimat paling gampang: **angka kondisi lahan masuk, tebakan nama tanaman keluar**. Kita tidak mengolah foto daun, tidak meramal harga, tidak menghitung ton panen, dan tidak menentukan berapa karung pupuk yang harus dibeli.

Nama aplikasi kita {APP_NAME}. Judul akademiknya: {TITLE}.

## Satu baris itu apa?
Baris pertama berisi N=90, P=42, K=43, suhu sekitar 20,88°C, kelembapan sekitar 82%, pH sekitar 6,50, hujan sekitar 202,94 mm, dan label rice atau padi.

Bahasa gampangnya: 'Dalam buku ini, kombinasi tujuh petunjuk itu diberi nama padi.' Komputer belajar meniru hubungan tersebut. Ini bukan bukti bahwa pengukuran itu berasal dari satu lahan tertentu, bahwa 2.200 baris adalah 2.200 lahan berbeda, atau bahwa panen padi di sana pasti berhasil. CSV tidak mempunyai ID lahan, tanggal pengukuran, lokasi, atau hasil panen.

## Apa yang dipelajari dan apa jawabannya?
- X = tujuh angka petunjuk: N, P, K, temperature, humidity, ph, rainfall.
- y = jawaban di buku: label jenis tanaman, misalnya rice atau maize.
- Saat belajar, X dan y sama-sama tersedia. Saat dipakai, pengguna hanya memberi X dan komputer menebak y.

Itulah supervised learning: belajar dengan contoh yang sudah ada jawabannya. Jenis tugasnya klasifikasi multikelas karena jawabannya satu nama dari 22 pilihan. Disebut rekomendasi karena nama hasil klasifikasi ditampilkan sebagai saran; ini bukan recommender system berbasis rating pengguna.

## Apa yang tidak boleh disalahpahami?
Nama tanaman bukan tombol untuk menyuruh tanaman tumbuh. Model tidak mengukur tanah sendiri. Nilai input harus didapat dari pengukuran atau data lingkungan yang definisinya sesuai sumber. Aplikasi ini tempat mencoba pola dataset, bukan alat pembuktian bahwa suatu tanaman paling menguntungkan.
"""),
        ("02_Dataset_dan_Arti_Kolom.md", f"""# 2. Isi buku datanya

Data lokal memiliki tepat 2.200 baris, delapan kolom, tujuh input numerik dan satu target kategorikal. Ada 22 tanaman; setiap tanaman memiliki tepat 100 contoh. Tidak ditemukan nilai kosong maupun baris duplikat.

Sumber yang dirujuk adalah Crop Recommendation Dataset oleh Atharva Ingle di Kaggle: {SOURCE_URL}. Berkas yang dipakai adalah CSV milik pengguna yang sudah ada di folder, tidak diganti dengan dataset lain. Hash asal ada di data/source_manifest.json.

## Tujuh petunjuk, versi gampang
- N atau nitrogen: unsur hara yang membantu pertumbuhan, termasuk bagian daun.
- P atau fosfor: unsur hara yang berperan dalam energi tanaman serta perkembangan akar dan reproduksi.
- K atau kalium: unsur hara yang membantu pengaturan air dan banyak fungsi tanaman. Analogi 'daya tahan' hanya penyederhanaan.
- Temperature: seberapa panas atau dingin udara, dalam derajat Celsius.
- Humidity: seberapa lembap udara, bukan kadar air tanah, dalam persen.
- pH: ukuran asam atau basa tanah, tanpa satuan. Bukan rasa yang boleh dicicipi; jangan mencicipi tanah.
- Rainfall: besarnya curah hujan, dalam mm. Periode akumulasinya tidak tercantum di CSV, jadi jangan asal menganggap hujan harian, bulanan atau tahunan.

{mdtable(['Kolom','Arti','Satuan/catatan','Rentang sumber'], rows)}

NPK dibaca sebagai angka kandungan/rasio sesuai skala dataset. Bukan persen komposisi kemasan pupuk dan bukan dosis kg pupuk per hektare. Kita belum memverifikasi satuan laboratoriumnya dari pengelola Kaggle. Jangan mengarang konversi dari sensor atau mg/kg.

## Kenapa datanya disebut seimbang?
Bayangin tiap tanaman kebagian 100 kartu latihan. Tidak ada yang cuma punya dua kartu sementara yang lain punya ribuan. Maka kita tidak memakai SMOTE, oversampling atau class weighting. Tidak semua teknik preprocessing harus dipakai.

## Dari mana konteks India dan augmentasi?
Thilakarathne et al. (2022), bagian 4, mendeskripsikan dataset Kaggle tersebut sebagai augmentasi data hujan, iklim, dan pupuk yang tersedia untuk India [R1]. Ini informasi dari literatur, bukan kesimpulan karena tabelnya rapi. Kita tidak memiliki catatan yang dapat mengaudit proses augmentasi tiap baris. Lisensi sumber juga perlu diperiksa sebelum redistribusi publik.

## Nama 22 tanaman
{', '.join(f'{k} ({v})' for k,v in CROP_NAMES.items())}.
"""),
        ("03_Alur_dan_Preprocessing.md", f"""# 3. Mengolahnya ngapain aja?

## Langkah 1 — Baca dan cek buku
Kita membuka CSV, melihat tipe angka, menghitung label, memeriksa data bolong, data dobel, nilai tidak valid dan statistik. Hasilnya: tidak ada missing atau duplikat. Maka kita tidak pura-pura mengisi missing yang tidak ada. Data aplikasi yang kosong justru ditolak agar tidak menebak dari pengukuran yang belum tersedia.

## Langkah 2 — Pisahkan bahan belajar dan ujian
Dari 2.200 contoh, kita sisihkan 1.760 untuk belajar dan 440 untuk ujian akhir. Stratify menjaga setiap tanaman punya 80 contoh training dan 20 test. Pembagiannya tetap: random_state=2026. Tidak mencoba banyak seed demi mendapatkan nilai bagus.

Sebelum paket ini, baseline eksploratif seed=42 sempat dilihat. Hasil final sekarang memakai protokol tertulis di kode, bukan klaim penelitian blind atau praregistrasi. Test final tidak digunakan memilih parameter atau pemenang, dan tidak diulang dengan pembagian baru untuk mempercantik angka.

## Langkah 3 — Lihat pola lewat EDA
Histogram seperti melihat sebaran tinggi badan anak-anak. Bar chart kelas menghitung jumlah kartu setiap tanaman. Boxplot membantu menandai angka jauh dari kelompoknya. Scatter menunjukkan dua angka sekaligus untuk melihat kelompok yang mirip. Heatmap korelasi menunjukkan hubungan linear antarf fitur, bukan bukti penyebab tanaman tumbuh.

Visualisasi fitur memakai training, bukan test. Pemeriksaan struktur dan distribusi kelas sumber hanya audit. Nilai K tinggi pada apel/anggur membentuk kelompok kelas dalam dataset; tidak otomatis berarti salah ukur. Kita menandai outlier dengan aturan IQR untuk diperiksa, tidak membuangnya otomatis. Tidak ada klaim bahwa semua outlier telah dibuktikan benar secara agronomis.

## Langkah 4 — Scaling: ubah skala, bukan ubah arti
pH bisa sekitar 6, sedangkan hujan bisa sekitar 200. Kalau KNN langsung menghitung jarak mentah, angka besar dapat lebih dominan. StandardScaler mengurangi angka dengan rata-rata training dan membaginya dengan simpangan baku training: z = (x - mean_train) / std_train.

Ini bukan mengganti semua satuan jadi sama dan bukan memaksa angka ke 0–1. Hasilnya bisa negatif. Analogi gampangnya: menaruh petunjuk pada ukuran relatif terhadap variasinya, sehingga jarak tidak semata-mata dikuasai besarnya angka mentah. Scaling tidak otomatis membuat semua fitur sama penting dan tidak menjamin akurasi naik.

KNN dan Logistic Regression memakai StandardScaler. Decision Tree tidak memerlukannya karena pertanyaan ambang mempertahankan urutan nilai meskipun skala diubah. Scaling dan model dibungkus Pipeline; scaler di-fit hanya pada training yang sedang dipakai di tiap fold, bukan seluruh data.

## Langkah 5 — Beri nomor pada nama tanaman
LabelEncoder mengubah nama menjadi ID 0 sampai 21. ID hanyalah kartu identitas, bukan urutan tanaman paling bagus. Encoder di-fit pada label training. Aplikasi mengubah nomor kembali menjadi nama dengan encoder yang sama. Label tidak dimasukkan ke kolom input.

## Data leakage itu apa?
Ibarat kunci ujian bocor sebelum ujian dimulai. Contoh yang salah: fit scaler pada semua 2.200 baris, baru membagi training dan test. Contoh yang benar: split dahulu; scaler belajar dari bagian training/fold saja. Test tidak boleh menentukan pilihan model.
"""),
        ("04_Tiga_Model_dan_Validasi.md", f"""# 4. Tiga murid, tiga cara belajar

## KNN — tanya tetangga yang mirip
Kalau ada kondisi baru, KNN mencari contoh training paling dekat. Nama tanaman dari tetangga menjadi dasar keputusan. k adalah jumlah tetangga. weights=distance memberi pengaruh lebih besar kepada tetangga dekat. p=1 menghitung jarak Manhattan; p=2 jarak Euclidean.

## Decision Tree — pertanyaan bercabang
Komputer belajar bertanya, misalnya 'hujannya di bawah angka ini?' lalu 'kelembapannya di atas angka itu?'. Ambang dan urutannya dipelajari dari training, bukan karangan kita. Pohon terlalu dalam dapat menghafal; pohon terlalu dangkal bisa tidak cukup membedakan 22 tanaman.

## Logistic Regression — nilai untuk setiap pilihan
Walau namanya regression, ini dipakai untuk klasifikasi. Tujuh angka dibobot menjadi skor tiap kelas, lalu diubah menjadi probabilitas kelas. Batas keputusannya linear dalam ruang tujuh fitur, bukan satu garis di kertas yang memisahkan semua 22 tanaman sekaligus. C mengatur kekuatan regularisasi: C besar berarti penalti lebih lemah.

Ketiganya menyediakan predict_proba, bukan hanya Logistic Regression. Namun skor belum dikalibrasi: skor 90% tidak otomatis berarti 90% peluang panen berhasil.

## Tuning itu mencoba setelan
KNN: k = 3/5/7/9/11; weights uniform/distance; p=1/2 (20 kombinasi). DT: max_depth 5/8/12/tanpa batas; daun minimal 1/2/4; gini/entropy (24 kombinasi). LR: C=0,01/0,1/1/10/100 (5 kombinasi), max_iter=3000.

## Kenapa nested CV?
Bayangin ada latihan ujian kecil di dalam ujian latihan besar. Outer CV membagi 1.760 training menjadi lima bagian; setiap giliran satu bagian jadi ujian validasi. Pada empat bagian lainnya, inner CV tiga fold membantu memilih setelan GridSearch. Setelah itu model terpilih di inner diuji pada bagian outer yang tidak dilihatnya.

Kita memperoleh lima skor outer untuk setiap keluarga model dan merata-ratakan macro-F1. Ini menilai proses tuning, bukan hanya skor terbaik dari banyak percobaan pada data validasi yang sama. Pemenang = mean terbesar; jika persis sama, SD terkecil lalu nama alfabetis. SD bukan confidence interval.

Sesudah keluarga model dipilih, GridSearch lima fold pada seluruh training mencari setelan final setiap model. Skor terbaik final GridSearch ada di tuning.json, tetapi bukan angka utama pembanding yang bebas bias seleksi. Test 440 contoh baru dihitung sesudah selection_before_test.json ditulis. Model aplikasi tidak dilatih ulang pada seluruh 2.200 baris, sehingga tetap identik dengan model yang dievaluasi.
"""),
        ("05_Hasil_dan_Analisis.md", f"""# 5. Hasil ujian yang benar-benar didapat

{tables(cv,test)}

## Siapa yang dipilih?
Model aplikasi adalah {best}. Pemilihannya mengikuti mean outer nested-CV macro-F1 tertinggi, bukan test accuracy. Mean validasinya {s['selected_cv']['cv_f1_macro_mean']:.6f} dengan SD {s['selected_cv']['cv_f1_macro_std']:.6f}. CV terendah pada konfigurasi ini adalah {weakest}.

Logistic Regression dan Decision Tree hampir seri. Selisih CV mereka hanya {abs(float(cv.set_index('model').loc['Logistic Regression','cv_f1_macro_mean'])-float(cv.set_index('model').loc['Decision Tree','cv_f1_macro_mean'])):.8f}. Ini jauh lebih kecil daripada variasi antarfold, jadi jangan mengatakan LR terbukti unggul secara statistik. Aturan pemilihan yang sudah tetap tetap diikuti; DT adalah alternatif yang layak dipertimbangkan pada penelitian validasi baru.

## Model dengan performa terendah dan kemungkinan penyebabnya
Pada validasi Nested CV, **{weakest}** memperoleh mean macro-F1 terendah ({cv.iloc[-1].cv_f1_macro_mean:.4f} ± {cv.iloc[-1].cv_f1_macro_std:.4f}) dan gap train–validasi terbesar ({cv.iloc[-1].cv_gap:.4f}). Kemungkinan penyebabnya adalah sifat KNN yang berbasis jarak lokal di ruang 7 fitur sehingga lebih sensitif terhadap tumpang tindih batas kelas antar-tanaman yang kondisinya berdekatan (tercermin pula pada kesalahan uji KNN seperti `rice→jute` 6 kasus dan `mothbeans→lentil` 4 kasus) serta sensitif terhadap pembobotan skala fitur (terlihat pada ablation scaling).

Pada evaluasi holdout test, **Logistic Regression** memperoleh akurasi terendah (0.9682, salah 14/440) dibanding KNN (0.9705) dan Decision Tree (0.9864). Kemungkinan penyebabnya adalah batas keputusan linear Logistic Regression kurang lentur memisahkan sedikit kasus perbatasan non-linear pada pasangan kelas yang sangat mirip (`rice→jute` 5 kasus, `lentil→mothbeans` 3 kasus) dibandingkan pemisahan ambang bercabang milik Decision Tree. Meskipun demikian, Logistic Regression tetap dipertahankan karena dipilih dari validasi sebelum test dibuka.

## Kok test terbaik malah berbeda?
Pada test, {top_test.model} mendapat macro-F1 tertinggi, {top_test.f1_macro:.4f}. Kita tetap memakai {best} karena kalau pemenang diganti setelah melihat test, test berubah menjadi alat pemilihan. Model aktif benar pada {int(s['selected_test']['n_correct'])} dari 440 contoh; salah pada {440-int(s['selected_test']['n_correct'])} contoh. Nilai test ini tidak membuktikan akurasi lapangan Indonesia.

## Cara membaca nilainya
- Accuracy: dari semua soal, berapa bagian yang benar.
- Precision tanaman padi: dari semua yang ditebak padi, berapa yang benar padi.
- Recall padi: dari semua contoh padi asli, berapa yang ditemukan model.
- F1: merangkum keseimbangan precision dan recall.
- Macro: hitung nilai masing-masing tanaman, lalu rata-rata dengan bobot sama.
- Confusion matrix: buku salah tebak. Baris adalah label sebenarnya, kolom adalah tebakan. Nilai diagonal berarti benar.

## Salahnya di mana?
{mdtable(['Aktual','Ditebak menjadi','Jumlah'], [[r.actual,r.predicted,r.count] for r in bp.itertuples()])}

Jumlah di tabel adalah kesalahan pada test model aktif, bukan hasil semua model digabung. Pasangan rice→jute paling menonjol pada model aktif, disusul lentil→mothbeans. Untuk analisis, lihat crop_means_train.csv, scatter_kemiripan.png, dan tujuh nilai tiap contoh salah di test_errors.csv. Padi/jute memiliki beberapa nilai NPK dan kelembapan yang dekat dalam training; hujan membantu membedakan, tetapi sebagian rentang bertumpang tindih. Ini penjelasan masuk akal dari pola data, bukan pembuktian sebab pasti satu prediksi salah.

## Menghafal atau memahami pola?
{mdtable(['Model','F1 train final','F1 nested CV','F1 test','Gap CV train-valid'], [[r.model,f'{test.set_index("model").loc[r.model,"train_f1_macro"]:.4f}',f'{r.cv_f1_macro_mean:.4f}',f'{test.set_index("model").loc[r.model,"f1_macro"]:.4f}',f'{r.cv_gap:.4f}'] for r in cv.itertuples()])}

KNN dengan pembobotan distance dapat memberi F1 training 1 karena setiap contoh menemukan dirinya sendiri. Nilai itu bukan jaminan generalisasi. Ada gap train-validasi dan train-test; ini indikasi optimisme/overfitting ringan pada konfigurasi yang diuji, bukan diagnosis pasti. Tidak terlihat underfitting berat pada model final karena skor training dan validasi tinggi. Perbedaan final train dengan mean CV tidak identik karena ukuran training dan tuning antarfold berbeda.

## Petunjuk mana yang dipakai pohon?
{mdtable(['Fitur','Importance DT'], [[r.feature,f'{r.importance:.4f}'] for r in imp.itertuples()])}

Tiga teratas adalah {', '.join(imp.head(3).feature)}. Ini impurity importance milik Decision Tree, bukan penjelasan lokal mengapa Logistic Regression memilih satu tanaman. Importance tidak membuktikan penyebab hasil panen, dapat dipengaruhi korelasi dan metode perhitungan. pH rendah importance bukan berarti pH tidak penting secara biologis.

## Scaling: hasilnya boleh tidak sesuai dugaan
{mdtable(['Model','Pakai scaling?','Mean CV F1','Setelan tetap'], [[r.model,r.scaling,f'{r.cv_f1_macro_mean:.4f}',r.setting] for r in sc.itertuples()])}

Pada KNN k=5 default, scaling justru menurunkan mean CV pada split ini. Artinya bobot implisit jarak mentah kebetulan lebih membantu konfigurasi ini; bukan bukti bahwa scaling selalu buruk. KNN final dituning di ruang scaled sesuai rancangan, sedangkan KNN unscaled hanya ablation CV dan tidak dipakai memilih ulang setelah test. DT menghasilkan skor sama pada ablation scaling; pohon depth=8 jauh lebih dangkal daripada konfigurasi final depth=12 sehingga skornya lebih rendah. Jangan membandingkan angka ablation depth=8 dengan hasil tuning final seolah modelnya sama.
"""),
        ("06_Aplikasi_dan_Cara_Menjalankan.md", f"""# 6. Dari buku latihan menjadi aplikasi

Alurnya: pengguna isi tujuh angka → kode memeriksa angka → pipeline tersimpan melakukan scaling jika perlu → model memprediksi → ID label dikembalikan ke nama tanaman → aplikasi menampilkan kelas dan tiga skor teratas.

Pipeline, encoder, urutan fitur, rentang training dan profil tanaman disimpan dalam models/crop_bundle.joblib. Aplikasi memeriksa hash berkas agar model tidak tertukar dengan hasil laporan. Jangan membuka joblib dari sumber asing; aplikasi tidak menerima unggahan model.

## Jalankan paling gampang di Windows
1. Buka folder proyek tanaman.
2. Klik INSTAL_DEPENDENCY.bat sekali untuk memasang paket, atau jalankan python -m pip install -r requirements.txt di terminal.
3. Klik JALANKAN_APLIKASI.bat, atau jalankan python -m streamlit run app.py.
4. Buka alamat yang dicetak terminal, biasanya http://localhost:8501.

Jangan menjalankan app.py dengan python biasa. Terminal server jangan ditutup selama aplikasi dipakai. Jika port sibuk: python -m streamlit run app.py --server.port 8502. Internet diperlukan untuk instalasi dan font opsional; model/data bekerja lokal.

## Isi form dan CSV
Menu Rekomendasi menyediakan contoh training, tujuh input angka, prediksi, tiga skor teratas, grafik, ringkasan min/median/max training dan unduh CSV. Menu CSV memerlukan tepat nama kolom N,P,K,temperature,humidity,ph,rainfall; urutan boleh berbeda karena kode menyusun ulang. Kolom tambahan diabaikan, label bukan input model.

CSV maksimal 5 MB dan 10.000 baris. Teks, angka tak hingga, nilai kosong, pH di luar 0–14, kelembapan di luar 0–100 dan NPK/hujan negatif ditolak. Nol tidak otomatis hilang: N=0 adalah angka valid dalam sumber. Angka di luar rentang training diberi peringatan; pemeriksaan rentang bukan detektor semua kombinasi asing.

## Membaca hasil dengan benar
Jika aplikasi menulis padi dengan skor 90%, artinya model menaruh skor 0,90 untuk kelas padi di antara 22 kelas yang dikenal. Ini bukan peluang panen berhasil. Tiga pilihan dapat mempunyai skor seri atau nol; pilihan nol bukan saran kuat. Min/median/max tanaman menggambarkan training, bukan kebutuhan ideal yang telah diverifikasi.

Kode tidak menyimpan input pengguna secara permanen. Jika aplikasi di-deploy online, data tetap dikirim ke server untuk diproses. Belum ada sistem akun, monitoring agronomis atau IoT. Link deployment: {config['deployment_url'] or 'BELUM DIBUAT; tidak mengklaim aplikasi sudah online.'}

## Membuat ulang proyek
Pasang requirements-dev.txt. Jalankan python train.py; python build_materials.py; python execute_notebook.py; python -m pytest -q; python capture_demo.py; lalu python build_materials.py untuk menyisipkan screenshot terbaru. Notebook mengeksekusi training ke folder audit sementara, tidak menimpa model utama. Perubahan dependency sklearn memerlukan training ulang dan pengujian ulang.
"""),
        ("07_Pertanyaan_Bayi_dan_Batasan.md", f"""# 7. Pertanyaan yang biasanya bikin bingung

## Jadi gua mengolah apa?
Kamu mengolah tabel contoh hubungan tujuh kondisi tanah/iklim dengan nama tanaman. Kamu mengecek kualitasnya, memahami pola, melatih tiga model, membandingkan kemampuan menebak label pada contoh yang tidak dilatih, lalu membuat aplikasi untuk memakai model terpilih.

## Kenapa bukan langsung cari tanaman dengan rata-rata paling dekat?
Itu bisa dijadikan baseline lain. Tiga model kita mempelajari batas atau kemiripan dengan cara berbeda; tidak hanya membandingkan satu rata-rata. Kita menguji mana yang bekerja pada prosedur yang sama, bukan menganggap satu cara selalu benar.

## Apakah 98% berarti petani pasti untung?
Tidak. Accuracy hanya menghitung kesesuaian tebakan dengan label sumber. Tidak ada data keuntungan atau hasil panen di CSV. Model bisa mendapat skor tinggi pada tabel tetapi gagal pada pengukuran lapangan yang definisinya berbeda.

## Kenapa Decision Tree tidak dipakai padahal test-nya bagus?
Karena pemilihan dilakukan di latihan validasi, sebelum membuka ujian akhir. Dalam eksperimen ini {best} menang sangat tipis di validasi. Mengganti pemenang setelah melihat test berarti memakai kunci ujian untuk memilih. Bila ingin mengubah aturan pemilihan, lakukan penelitian baru dengan evaluasi eksternal baru, bukan mengklaim holdout lama tetap independen.

## Kenapa tidak buang outlier dan tidak SMOTE?
Karena teknik bukan hiasan. Data kelas sudah seimbang. Angka ekstrem bisa menjadi ciri kelompok tanaman. Kita tidak punya bukti semua nilai ekstrem salah, jadi tidak menghapusnya sembarangan. Setiap tindakan harus ada alasan dan hasil pemeriksaannya.

## Kenapa tujuh angka tidak cukup untuk keputusan sungguhan?
Budidaya juga dipengaruhi varietas, tekstur tanah, air irigasi, hama, musim, lokasi, modal, harga, dan cara pengelolaan. CSV tidak mempunyai variabel itu. Model juga tidak punya pilihan 'tanaman baru di luar 22 kelas'. Ia tetap dapat menebak ketika inputnya asing.

## Batasan yang wajib disebut
- Konteks data India; belum ada validasi data lahan Indonesia atau pemisahan per wilayah/tahun.
- Literatur menyebut augmentasi; rasio data asli/sintetis dan ketergantungan antarsampel tidak dapat diaudit dari CSV.
- Split acak dan CV yang tinggi belum menguji generalisasi ke musim/lokasi baru.
- Satuan NPK dan periode rainfall perlu konfirmasi; aplikasi tidak memberikan konversi sensor atau dosis pupuk.
- Probabilitas belum dikalibrasi, hanya ada 22 kelas, dan tidak ada deteksi out-of-distribution yang andal.
- Profil min/median/max bukan 'kondisi ideal'. Tidak ada hasil panen untuk membuktikan rekomendasi terbaik.
- Selisih model sangat kecil, bukan bukti keunggulan signifikan. Pengujian eksternal dan uji agronomis masih diperlukan.

## Pengembangan masuk akal
Kumpulkan data ber-ID lahan/waktu/lokasi di Indonesia, verifikasi satuan dan label bersama ahli pertanian, gunakan split kelompok/waktu, kalibrasi probabilitas menggunakan training, tambah fitur relevan, evaluasi input asing, dan uji manfaat rekomendasi terhadap hasil panen nyata.

## Kesimpulan satu napas
Kita mengajari tiga murid membaca tujuh petunjuk untuk menebak satu dari 22 tanaman. Mereka latihan dari 1.760 contoh, diadu dengan nested CV, lalu diuji pada 440 contoh. {best} dipakai dalam aplikasi sesuai aturan validasi. Ini alat belajar pola data, bukan mesin penjamin panen.
"""),
        ("08_Identitas_dan_Checklist.md", f"""# 8. Identitas, tugas dan checklist pengumpulan

Kelompok: {config['group_name']}. Kelas: {config['class']}. Aplikasi: {APP_NAME}.

{tasks}

Seluruh anggota wajib memahami keseluruhan kode, data, metodologi, dan evaluasi. Nilai kelompok tidak menghapus kewajiban presentasi dan tanya jawab individu.

## Berkas pengumpulan
- PPT Laporan Project (Bagian A–O, template resmi kelompok): `presentation/Laporan_Proyek_Tanaman.pptx` (beserta PDF cadangan).
- Dokumen Portofolio Project CLASS-IPB: `docs/TEK1302_Kelompok7.docx`.
- Notebook ber-output: `PROJEK_TANAMAN.ipynb`.
- Source code: `app.py`, `crop_core.py`, `train.py`, `build_materials.py`, `build_ppt_template.py`, `tests/test_project.py`, `requirements.txt`.
- Dataset: `Crop_recommendation.csv`, sumber/hash di `data/source_manifest.json`.
- Model terlatih: `models/crop_bundle.joblib` (+ 3 pipeline final).
- Buku penjelasan bahasa sederhana: `docs/Penjelasan_Tanaman_Bahasa_Sederhana.docx`.
- Lima jurnal referensi: `references/Daftar_5_Jurnal.md`, PDF (`R2`–`R5`), full-text (`R1`), DOI, dan metadata Crossref.
- Tabel studi literatur: `references/Tabel_Studi_Literatur.csv` dan `.md`, juga diringkas dalam PPT/Word.
- Bahan rekaman layar aplikasi: `video/demo_aplikasi.mp4` + naskah `video/Naskah_Demo_6_Menit_40_Detik.md`.
- Deployment bersifat opsional; petunjuk di `docs/09_Deployment.md`.

## Langkah akhir sebelum unggah
Rekam/tambahkan perkenalan dan narasi ketiga anggota pada video demo (maksimal 7 menit, memperlihatkan aplikasi {APP_NAME} berjalan nyata). Rename folder pengumpulan sesuai format `ML2026_Kelas_NamaKelompok_JudulProject` (contoh: `ML2026_TEK1302_Kelompok7_TunasMatch`).

AI membantu penyusunan kode, dokumentasi, dan debugging. Seluruh angka evaluasi berasal dari eksekusi nyata; mahasiswa bertanggung jawab memahami, menjalankan ulang, dan menjelaskan seluruh hasil.
"""),
    ]
    for filename, content in sections: write(ROOT / "docs" / filename, content)
    return sections


def md_to_doc(doc, text):
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line: i += 1; continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [v.strip().replace("**", "") for v in lines[i].strip().strip("|").split("|")]
                if not all(set(v) <= set("-: ") for v in cells): rows.append(cells)
                i += 1
            table = doc.add_table(rows=1, cols=len(rows[0])); table.style = "Light Shading Accent 1"
            for c,v in zip(table.rows[0].cells, rows[0]): c.text = v
            for row in rows[1:]:
                for c,v in zip(table.add_row().cells,row): c.text = v
            continue
        if line.startswith("### "): doc.add_heading(line[4:], level=3)
        elif line.startswith("## "): doc.add_heading(line[3:], level=2)
        elif line.startswith("# "): doc.add_heading(line[2:], level=1)
        elif line.startswith("- "): doc.add_paragraph(line[2:].replace("**", ""), style="List Bullet")
        else: doc.add_paragraph(line.replace("**", "").replace("`", ""))
        i += 1


def build_word(sections, config):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = section.bottom_margin = Cm(1.8)
    section.left_margin = section.right_margin = Cm(1.9)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"; normal.font.size = DPt(11)
    normal.paragraph_format.space_after = DPt(7)
    normal.paragraph_format.line_spacing = 1.12
    for name in ["Title", "Heading 1", "Heading 2", "Heading 3"]:
        doc.styles[name].font.name = "Calibri"
        doc.styles[name].font.color.rgb = DColor.from_string("236543")
    doc.add_paragraph("TunasMatch", "Title")
    doc.add_paragraph("Buku penjelasan proyek tanaman\nBahasa sederhana, dari nol sampai aplikasi", "Subtitle")
    doc.add_paragraph(TITLE)
    doc.add_paragraph(f"{config['group_name']} | Kelas {config['class']}\nData, alur, alasan, hasil nyata, dan persiapan tanya jawab.")
    doc.add_paragraph("Baca bagian 1–4 dahulu kalau baru mulai. Bagian 5 menjelaskan angka hasil. Bagian 6 membantu menjalankan aplikasi, dan bagian 7–8 untuk batasan serta pengumpulan.")
    doc.add_paragraph("Penting: ini klasifikasi label dataset. Bukan jaminan sukses panen atau panduan dosis pupuk.")
    doc.add_page_break()
    doc.add_heading("Daftar isi singkat", 1)
    for _,content in sections: doc.add_paragraph(content.splitlines()[0].lstrip("# "))
    doc.add_paragraph("Lampiran: gambar, studi literatur, peta kode, dan naskah menjelaskan proyek.")
    for _, content in sections:
        doc.add_page_break(); md_to_doc(doc, content)
    doc.add_page_break(); doc.add_heading("Lampiran A — Membaca grafik", 1)
    images = [("distribusi_kelas.png", "Jumlah kelas sama: jangan mengada-ada masalah imbalance."),
              ("scatter_kemiripan.png", "Titik yang berdekatan menunjukkan sebagian kondisi mirip; dua fitur tidak mewakili seluruh ruang tujuh fitur."),
              ("perbandingan_cv.png", "Skor validasi memilih keluarga model. Garis error adalah SD lima fold."),
              ("pasangan_tertukar.png", "Kesalahan model aktif: cek arah aktual menuju prediksi."),
              ("feature_importance.png", "Peringkat ini hanya impurity importance Decision Tree; bukan kesimpulan biologis."),
              ("scaling.png", "Percobaan scaling memakai setelan tetap, bukan membandingkan dua model final hasil tuning.")]
    for filename, caption in images:
        doc.add_heading(caption, 2)
        doc.add_picture(str(ROOT / "plots" / filename), width=Cm(16.4))
    doc.add_page_break(); doc.add_heading("Lampiran B — Lima jurnal dan studi literatur", 1)
    for r in REFERENCES:
        doc.add_heading(f"[{r['id']}] {r['authors']} ({r['year']})", 2)
        doc.add_paragraph(f"{r['title']}. {r['journal']}. https://doi.org/{r['doi']}")
        for key, name in [("problem","Masalah"),("dataset","Dataset"),("methods","Metode"),("metrics","Metrik"),("result","Hasil artikel"),("difference","Perbedaan"),("evidence","Catatan verifikasi")]:
            doc.add_paragraph(f"{name}: {r[key]}")
    doc.add_page_break(); doc.add_heading("Lampiran C — Peta kode, versi gampang", 1)
    for file,desc in [("crop_core.py","kamus kolom, pemeriksa input, pemuat model dan fungsi prediksi"), ("train.py","dapur eksperimen: split, EDA, tuning, CV, evaluasi, simpan model"), ("PROJEK_TANAMAN.ipynb","buku belajar interaktif yang menjalankan alur sama dengan hasil tertanam"), ("app.py","halaman web untuk memasukkan angka dan membaca hasil"), ("build_materials.py","mengambil hasil nyata untuk membuat PPT, Word dan panduan"), ("tests/test_project.py","pemeriksaan otomatis agar input dan hasil tidak tertukar"), ("results/","bukti angka: split, fold, metrik, label dan kesalahan"), ("plots/","gambar EDA dan evaluasi"), ("models/","resep/model yang sudah belajar, bukan data input pengguna")]:
        doc.add_paragraph(f"{file}: {desc}", "List Bullet")
    doc.add_heading("Kalimat singkat untuk menjelaskan di depan dosen", 2)
    doc.add_paragraph("Kami mengolah 2.200 contoh tanah dan iklim dengan tujuh fitur dan 22 label tanaman. Data seimbang, tanpa missing dan duplikat. Kami membandingkan KNN, Decision Tree, dan Logistic Regression dengan split stratified 80:20, pipeline scaling dan nested CV untuk tuning. Model dipilih berdasarkan validasi, lalu hasil test dilaporkan tanpa memilih ulang. Kami menganalisis kesalahan kelas serta fitur pohon dan membangun aplikasi Streamlit. Skor adalah kesesuaian terhadap label dataset, bukan jaminan keberhasilan budidaya.")
    footer = section.footer.paragraphs[0]
    footer.text = f"{APP_NAME} • {config['group_name']} • {config['class']} • Penjelasan sederhana"
    footer.runs[0].font.size = DPt(9)
    doc.save(ROOT / "docs/Penjelasan_Tanaman_Bahasa_Sederhana.docx")


def build_portfolio_doc(s, config, cv, test):
    """Dokumen khusus unggahan tugas 'Portofolio Project' di CLASS-IPB (format KELAS_KELOMPOK)."""
    doc = Document()
    section = doc.sections[0]
    section.top_margin = section.bottom_margin = Cm(2.0)
    section.left_margin = section.right_margin = Cm(2.2)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = DPt(11)
    normal.paragraph_format.space_after = DPt(6)
    normal.paragraph_format.line_spacing = 1.15
    for name in ["Title", "Heading 1", "Heading 2"]:
        doc.styles[name].font.name = "Calibri"
        doc.styles[name].font.color.rgb = DColor.from_string("223915")

    doc.add_paragraph(f"PORTOFOLIO PROJECT AKHIR — {APP_NAME.upper()}", "Title")
    doc.add_paragraph(TITLE, "Subtitle")

    doc.add_heading("1. Identitas Kelompok & Judul Project", 1)
    doc.add_paragraph(f"Nama Aplikasi / Brand: {APP_NAME}")
    doc.add_paragraph(f"Kelompok: {config['group_name']}")
    doc.add_paragraph(f"Kelas / Mata Kuliah: {config['class']}")
    t_mem = doc.add_table(rows=1, cols=3)
    t_mem.style = "Light Shading Accent 1"
    for c, h in zip(t_mem.rows[0].cells, ["Nama Anggota", "NIM", "Pembagian Tugas"]):
        c.text = h
    for m in config["members"]:
        row = t_mem.add_row().cells
        row[0].text, row[1].text, row[2].text = m["name"], m["nim"], m["task"]

    doc.add_heading("2. Tautan Jurnal Referensi Utama (5 Artikel Ilmiah)", 1)
    for r in REFERENCES:
        doc.add_paragraph(
            f"[{r['id']}] {r['authors']} ({r['year']}). {r['title']}. {r['journal']}. DOI: https://doi.org/{r['doi']} | Tautan: {r['url']}",
            style="List Bullet",
        )

    doc.add_heading("3. Tautan Dataset & Aplikasi", 1)
    doc.add_paragraph(f"Dataset sumber: Crop Recommendation Dataset (Atharva Ingle, Kaggle) — {SOURCE_URL}")
    doc.add_paragraph(f"Berkas lokal: Crop_recommendation.csv (SHA-256: {s['dataset_sha256']}), 2.200 baris × 8 kolom, 7 fitur numerik (N, P, K, temperature, humidity, ph, rainfall), 22 kelas tanaman seimbang (100/kelas), 0 missing, 0 duplikat.")
    dep = config.get("deployment_url") or "Aplikasi dijalankan lokal melalui Streamlit (python -m streamlit run app.py atau JALANKAN_APLIKASI.bat); deployment cloud bersifat opsional."
    doc.add_paragraph(f"Aplikasi Web ({APP_NAME}): {dep}")

    doc.add_heading("4. Penjelasan Implementasi Machine Learning", 1)
    doc.add_heading("4.1 Preprocessing Data (Bebas Data Leakage)", 2)
    doc.add_paragraph(
        "Dataset telah diaudit lengkap (0 missing, 0 duplikat) dan seimbang sempurna (100 contoh/kelas), sehingga tidak dilakukan imputasi buatan ataupun SMOTE/class weighting. "
        "Outlier yang ditandai IQR ditinjau per kelas (misalnya Kalium tinggi mengelompok secara konsisten pada apel dan anggur) sehingga tidak dihapus otomatis. "
        "Target 22 nama tanaman dikodekan dengan LabelEncoder yang di-fit pada data latih saja. StandardScaler (z = (x − μ_train) / σ_train) dibungkus dalam sklearn Pipeline khusus untuk KNN dan Logistic Regression (Decision Tree tanpa scaler) agar parameter skala hanya dipelajari dari data latih/fold latih."
    )
    doc.add_heading("4.2 Training, Validasi, dan Testing", 2)
    doc.add_paragraph(
        "Data dibagi dengan Stratified Split 80:20 (seed=2026) menjadi 1.760 data training (80/kelas) dan 440 data testing (20/kelas). "
        "Perbandingan tiga algoritma (KNN, Decision Tree, Logistic Regression) menggunakan Nested Cross-Validation pada training saja (outer StratifiedKFold 5-fold, inner GridSearchCV 3-fold dengan skor macro-F1), diikuti final GridSearchCV 5-fold pada seluruh 1.760 training. "
        "Keluarga model terbaik ditetapkan dan dicatat (results/selection_before_test.json) sebelum holdout test dibuka. Model aplikasi tidak di-refit ke seluruh 2.200 baris sehingga 100% identik dengan model yang diuji."
    )
    doc.add_heading("4.3 Evaluasi dan Perbandingan Model", 2)
    merged = cv.merge(test, on="model")
    t_eval = doc.add_table(rows=1, cols=6)
    t_eval.style = "Light Shading Accent 1"
    for c, h in zip(t_eval.rows[0].cells, ["Model", "Nested CV Macro-F1 ± SD", "Test Acc", "Precision Macro", "Recall Macro", "F1 Macro"]):
        c.text = h
    for r in merged.itertuples():
        cells = t_eval.add_row().cells
        cells[0].text = r.model + (" (Aktif)" if r.model == s["selected_model"] else "")
        cells[1].text = f"{r.cv_f1_macro_mean:.6f} ± {r.cv_f1_macro_std:.4f}"
        cells[2].text = f"{r.accuracy:.4f}"
        cells[3].text = f"{r.precision_macro:.4f}"
        cells[4].text = f"{r.recall_macro:.4f}"
        cells[5].text = f"{r.f1_macro:.4f}"

    doc.add_heading("5. Analisis Mendalam: Integritas Pemilihan Model, Kesalahan Per Kelas, dan Ablation Scaling", 1)
    doc.add_paragraph(
        "1) Mengapa tidak memilih model berdasarkan Test Accuracy tertinggi? Pada holdout test, Decision Tree memperoleh akurasi 98,64% (434/440 benar), lebih tinggi dari Logistic Regression (96,82%, 426/440 benar). "
        "Namun pada Nested CV training, Logistic Regression unggul tipis (0,985205 vs 0,985203) dengan gap train–validasi paling kecil (0,0081 vs DT 0,0122 dan KNN 0,0176). "
        "Mengganti pemenang setelah melihat data uji akan melanggar prinsip independensi test set (data leakage seleksi). Selisih LR–DT sangat kecil sehingga tidak diklaim signifikan secara statistik."
    )
    doc.add_paragraph(
        "2) Analisis Model Performa Terendah & Pasangan Kelas Tertukar: KNN memiliki mean Nested CV terendah (0,9824) karena sensitivitas jarak lokal pada tumpang tindih 7 fitur (6 rice→jute, 4 mothbeans→lentil di test). "
        "Pada model aktif Logistic Regression, 14 kesalahan uji terkonsentrasi pada rice→jute (5 kasus) dan lentil→mothbeans (3 kasus), selaras dengan EDA bahwa sebagian kombinasi NPK dan kelembapan antar-pasangan tersebut berdekatan sementara curah hujan tidak sepenuhnya memisahkan batas linear."
    )
    doc.add_paragraph(
        "3) Ablation Scaling & Feature Importance: Pada percobaan ablation CV training (KNN k=5, DT max_depth=8), scaling KNN k=5 justru menurunkan mean CV macro-F1 dari 0,9785 menjadi 0,9714, sedangkan DT identik (0,8045) karena invarian terhadap transformasi monotonik. "
        "Feature importance kandidat Decision Tree menempatkan rainfall (0,3683), humidity (0,2239), dan P (0,2103) di posisi teratas. Hasil ini dilaporkan jujur beserta batasannya (konteks data India/augmentasi, probabilitas belum dikalibrasi, dan belum diuji pada lahan nyata Indonesia)."
    )

    footer = section.footer.paragraphs[0]
    footer.text = f"{APP_NAME} • {config['group_name']} • {config['class']} • Portofolio Project CLASS-IPB"
    footer.runs[0].font.size = DPt(9)
    doc.save(ROOT / "docs/TEK1302_Kelompok7.docx")


def build_notebook():
    cells = []
    md = lambda t: cells.append(nbf.v4.new_markdown_cell(t))
    code = lambda t: cells.append(nbf.v4.new_code_cell(t.strip()))
    md(f"# {APP_NAME} — Proyek Klasifikasi Tanaman\n\n{TITLE}\n\nNotebook end-to-end: memahami data → EDA → preprocessing → nested CV/GridSearch → evaluasi → analisis → simpan model → inferensi. Seluruh angka berasal dari eksekusi. Edit identitas di `group_config.json`.\n\n**Tidak memodifikasi dataset asli atau model utama saat Run All.** Training dijalankan ke folder audit sementara. `train.py` menyimpan alur yang sama agar notebook dan aplikasi tidak berbeda resep.")
    md("## 1. Persiapan\nJalankan `python -m pip install -r requirements-dev.txt` dahulu. Notebook dapat dibuka dari folder proyek atau parent workspace. Tidak memerlukan unduhan dataset.")
    code('''from pathlib import Path
import sys, os, tempfile, inspect, json
import pandas as pd
import numpy as np
from IPython.display import display, Image, Markdown
root = Path.cwd()
if not (root / 'crop_core.py').exists():
    matches = [p.parent for p in root.glob('*/crop_core.py')]
    if matches:
        root = matches[0]
assert (root / 'crop_core.py').exists(), 'Buka notebook dari folder proyek TunasMatch atau parent workspace.'
sys.path.insert(0, str(root))
from crop_core import FEATURES, DISPLAY, SEED, load_dataset, read_json, predict_frame
from train import candidates, run_training
print('Seed final:', SEED)
display(read_json(root / 'group_config.json'))''')
    md("## 2. Loading dan audit dataset\nSatu baris adalah satu contoh berlabel, bukan bukti pengukuran lahan unik. NPK memakai skala sumber; periode rainfall belum terverifikasi.")
    code("df = load_dataset()\nprint('Bentuk:', df.shape)\ndisplay(df.head())\ndf.info()\ndisplay(df.describe().T)")
    code("display(df.isna().sum().rename('missing'))\nprint('Duplikat:', df.duplicated().sum())\ndisplay(df.label.value_counts().sort_index())\nassert df.shape == (2200, 8)\nassert (df.label.value_counts() == 100).all()")
    md("**Interpretasi:** data 22 kelas seimbang; tidak perlu SMOTE. Tidak ada nilai kosong atau duplikat sehingga tidak melakukan imputasi/deduplikasi palsu. Ketidakadaan missing bukan bukti data lapangan berkualitas sempurna.")
    md("## 3. Pisahkan X/y dan split 80:20 stratified\nTest tidak dipakai menghitung scaler, memilih parameter, atau menentukan pemenang. Indeks akan disimpan oleh eksperimen. Baseline eksploratif seed 42 pernah diperiksa; final memakai seed 2026 tetap, bukan mencari seed terbaik.")
    code('''from sklearn.model_selection import train_test_split
ids_train, ids_test = train_test_split(np.arange(len(df)), test_size=.2, random_state=SEED, stratify=df.label)
X_train = df.iloc[ids_train][FEATURES]
y_train = df.iloc[ids_train].label
X_test = df.iloc[ids_test][FEATURES]
y_test = df.iloc[ids_test].label
print('Training:', len(X_train), 'Test:', len(X_test))
display(pd.DataFrame({'train':y_train.value_counts(), 'test':y_test.value_counts()}).sort_index())
assert not set(ids_train) & set(ids_test)''')
    md("## 4. EDA training sebelum model\nGrafik fitur memakai training saja; distribusi kelas sumber adalah audit. Setiap grafik berikut diberi penjelasan, bukan hanya gambar.")
    code('''import matplotlib.pyplot as plt
import seaborn as sns
X_train.hist(figsize=(12, 7), bins=20, color='#27835d')
plt.suptitle('Histogram tujuh fitur training'); plt.tight_layout(); plt.show()
display(X_train.corr().round(3))''')
    md("**Baca histogram:** skala NPK, hujan dan pH berbeda; beberapa distribusi multimodal karena gabungan 22 tanaman. StandardScaler bukan pengubah ke 0–1. Korelasi hanya hubungan linear, bukan penyebab atau korelasi label numerik yang bermakna ordinal.")
    code('''q1, q3 = X_train.quantile(.25), X_train.quantile(.75)
iqr = q3-q1
display(((X_train < q1-1.5*iqr) | (X_train > q3+1.5*iqr)).sum().rename('ditandai_IQR'))
print('Tidak otomatis menghapus nilai yang ditandai.')''')
    md("**Baca outlier:** angka ekstrem perlu dilihat per kelas; K tinggi terkumpul pada apel/anggur dalam sumber. Tidak otomatis salah, tetapi juga tidak mengklaim seluruhnya terbukti valid secara agronomis. Kode tidak membuang data berdasarkan IQR.")
    md("## 5. Model, pipeline dan ruang GridSearch\nKNN dan LR: scaler → classifier. DT: classifier tanpa scaler. Encoder di-fit dari label training; label bukan fitur. Pipeline di-fit ulang dalam setiap fold untuk mencegah leakage.")
    code("for name, (pipeline, grid) in candidates().items():\n    print(name)\n    display(pipeline)\n    display(grid)")
    md("## 6. Jalankan eksperimen lengkap\nOuter StratifiedKFold=5, inner GridSearchCV=3 fold pada training; mean outer macro-F1 memilih keluarga model. Kemudian final GridSearch=5 fold pada seluruh training. Test dihitung setelah pilihan ditulis. SD antarfold bukan confidence interval; keunggulan sangat tipis tidak signifikan secara otomatis.\n\nKode lengkap dapat dibaca pada cell berikut dan `train.py`. Output audit tidak menimpa artefak proyek utama.")
    code("print(inspect.getsource(run_training))")
    code('''temp_parent = Path(os.environ.get('LOCALAPPDATA', str(root))) / 'Temp' / 'opencode'
temp_parent.mkdir(parents=True, exist_ok=True)
audit = tempfile.TemporaryDirectory(prefix='crop_notebook_', dir=temp_parent)
RUN_DIR = Path(audit.name)
summary = run_training(output_dir=RUN_DIR)
display(summary)''')
    md("## 7. Baca hasil EDA tersimpan\nDistribusi kelas: sama-sama 100. Boxplot: tinjau nilai ekstrem, jangan hapus otomatis. Scatter: tanaman dapat bertumpang tindih pada dua fitur; classifier memakai tujuh fitur.")
    code("for name in ['distribusi_kelas.png', 'boxplot.png', 'kalium_per_kelas.png', 'korelasi.png', 'scatter_kemiripan.png']:\n    display(Image(filename=str(RUN_DIR / 'plots' / name)))")
    md("## 8. Validasi, tuning dan ujian akhir\nPilih model berdasarkan outer CV, bukan test. Skor final GridSearch cenderung optimistis untuk kandidat pemenang tuning; jangan menggantikannya dengan outer score. Seluruh 22 label mendapat bobot sama pada macro-F1.")
    code("cv = pd.read_csv(RUN_DIR / 'results/cv_comparison.csv')\ntest = pd.read_csv(RUN_DIR / 'results/test_comparison.csv')\ndisplay(cv)\ndisplay(read_json(RUN_DIR / 'results/tuning.json'))\ndisplay(read_json(RUN_DIR / 'results/selection_before_test.json'))\ndisplay(test)")
    code("best = summary['selected_model']\nprint('Model aktif:', best)\nprint('Selisih dua CV teratas:', cv.iloc[0].cv_f1_macro_mean - cv.iloc[1].cv_f1_macro_mean)\nprint('Test tertinggi:', test.sort_values('f1_macro', ascending=False).iloc[0].model)\ndisplay(Image(filename=str(RUN_DIR / 'plots/perbandingan_cv.png')))\ndisplay(Image(filename=str(RUN_DIR / 'plots/train_cv_test.png')))")
    md("**Interpretasi:** LR dan DT hampir seri pada validasi; aturan tetap memilih mean tertinggi. DT unggul di test, tetapi tidak dipakai memilih ulang. KNN distance dapat memberi train=1 karena titik menjadi tetangga dirinya. Skor test tinggi tidak membuktikan generalisasi ke Indonesia.")
    md("## 9. Confusion matrix dan kesalahan tiap kelas\nBaris=aktual, kolom=prediksi; diagonal benar. Periksa arah pasangan, bukan menyebut semua kesalahan kacang-kacangan tanpa membaca hasil.")
    code("for name in ['KNN', 'Decision Tree', 'Logistic Regression']:\n    display(Image(filename=str(RUN_DIR / f'plots/confusion_{name.replace(\" \", \"_\")}.png')))\nreports = read_json(RUN_DIR / 'results/classification_reports.json')\ndisplay(pd.DataFrame({k:v for k,v in reports[best].items() if isinstance(v,dict)}).T)")
    code("pairs = pd.read_csv(RUN_DIR / 'results/confused_pairs.csv')\nerrors = pd.read_csv(RUN_DIR / 'results/test_errors.csv')\ndisplay(pairs[pairs.model == best])\ndisplay(errors[errors.model == best])\nmeans = pd.read_csv(RUN_DIR / 'results/crop_means_train.csv', index_col=0)\ndisplay(means.loc[['rice','jute','lentil','mothbeans']].round(2))")
    md("**Interpretasi:** kemiripan sejumlah NPK/kelembapan pada rice dan jute membantu menjelaskan risiko tertukar, sementara hujan dapat membedakan. Lihat angka contoh salah untuk menguji dugaan, bukan menganggap mean kelas penyebab pasti. Detail nested out-of-fold juga tersedia dan bukan prediksi in-sample.")
    code("oof = pd.read_csv(RUN_DIR / 'results/oof_predictions.csv')\ndisplay(oof.groupby('model').correct.agg(['mean','count']))\ndisplay(oof[(oof.model == best) & (~oof.correct)].head(15))")
    md("## 10. Fitur DT dan overfitting\nImportance DT bukan penjelasan lokal LR dan bukan bukti pentingnya fitur terhadap hasil panen. Fitur berkorelasi dapat saling menggantikan.")
    code("display(pd.read_csv(RUN_DIR / 'results/feature_importance_dt.csv'))\ndisplay(Image(filename=str(RUN_DIR / 'plots/feature_importance.png')))\ndisplay(Image(filename=str(RUN_DIR / 'plots/pohon_ringkas.png')))")
    md("## 11. Percobaan scaling sebelum/sesudah\nSetting tetap KNN k=5 dan DT depth=8; CV training yang sama, bukan test. DT final hasil tuning berbeda dari DT ablation depth=8.")
    code("scaling = pd.read_csv(RUN_DIR / 'results/scaling_experiment.csv')\ndisplay(scaling)\ndisplay(Image(filename=str(RUN_DIR / 'plots/scaling.png')))")
    md("**Interpretasi aktual:** scaling menurunkan skor KNN k=5 pada eksperimen ini; jangan menyembunyikan hasil. Scaling tetap mengatasi ketergantungan terhadap skala mentah, bukan menjamin skor naik. DT ablation menghasilkan skor sama; depth=8 dapat terlalu dangkal untuk 22 kelas. KNN tanpa scaling bukan kandidat pemilihan utama dalam rancangan ini.")
    md("## 12. Simpan/muat model dan prediksi input baru\nBundle sudah tersimpan oleh run_training: pipeline + label encoder + urutan fitur + rentang/profil training. Hanya muat joblib lokal tepercaya.")
    code('''import joblib
bundle = joblib.load(RUN_DIR / 'models/crop_bundle.joblib')
example = pd.read_csv(RUN_DIR / 'examples/contoh_batch.csv').head(3)
result, probabilities = predict_frame(example, bundle)
display(result)
display(probabilities)
assert np.allclose(probabilities.sum(axis=1), 1)
print('Artefak audit disimpan:', RUN_DIR / 'models/crop_bundle.joblib')''')
    md("## 13. Audit konsistensi terhadap paket utama\nModel aplikasi tidak direfit dengan test; hasil eksperimen dari kode yang sama seharusnya identik pada environment ini.")
    code("main_cv = pd.read_csv(root / 'results/cv_comparison.csv')\nmain_test = pd.read_csv(root / 'results/test_comparison.csv')\npd.testing.assert_frame_equal(cv, main_cv, check_exact=False, rtol=1e-10)\npd.testing.assert_frame_equal(test, main_test, check_exact=False, rtol=1e-10)\nassert summary['selected_model'] == read_json(root / 'results/summary.json')['selected_model']\nprint('Konsisten: CV, test, dan model terpilih.')")
    md("## 14. Implementasi dan batasan\nJalankan `python -m streamlit run app.py`. Aplikasi tidak fit model pada input pengguna, memeriksa skema angka, memberi peringatan rentang dan menampilkan skor tiga kelas. Skor bukan peluang panen; kondisi training bukan kondisi ideal agronomis.\n\nDataset terkait India dan literatur menyebut augmentasi; protokol asli, satuan NPK, periode hujan serta ketergantungan antarsampel belum terverifikasi. Tidak ada hasil panen, harga, hama, varietas, lokasi/waktu. Validasi eksternal Indonesia masih diperlukan. Selisih CV yang tipis bukan bukti keunggulan signifikan.")
    md("## 15. Referensi\n" + "\n".join(f"- [{r['id']}] {r['authors']} ({r['year']}). {r['title']}. https://doi.org/{r['doi']}" for r in REFERENCES) + "\n\nLihat `references/Tabel_Studi_Literatur.md` untuk masalah, dataset, metode, metrik, hasil dan perbedaan tiap artikel.")
    code("audit.cleanup()\nprint('Folder audit sementara dibersihkan; output notebook tetap tertanam dan model utama tidak berubah.')")
    nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name":"python3", "display_name":"Python 3", "language":"python"}, "language_info":{"name":"python"}})
    # Jangan menghapus notebook ber-output ketika hanya memperbarui identitas/PPT.
    target = ROOT / "PROJEK_TANAMAN.ipynb"
    if not target.exists(): nbf.write(nb, target)
    nbf.write(nb, ROOT / "docs/Template_Notebook_Tanpa_Output.ipynb")


class Deck:
    def __init__(self):
        self.prs = Presentation(); self.prs.slide_width = Inches(13.333); self.prs.slide_height = Inches(7.5)
        self.green = "236543"; self.dark = "173D30"; self.gold = "D8A94A"

    def shape(self, slide, x,y,w,h, color, kind=MSO_SHAPE.RECTANGLE):
        s = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
        s.fill.solid(); s.fill.fore_color.rgb = RGBColor.from_string(color); s.line.fill.background()
        return s

    def text(self, slide, text, x,y,w,h, size=22, color="173D30", bold=False):
        tf = slide.shapes.add_textbox(Inches(x),Inches(y), Inches(w), Inches(h)).text_frame
        tf.word_wrap = True
        for i, line in enumerate(str(text).split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = line; p.font.name = "Aptos"; p.font.size = Pt(size); p.font.bold = bold
            p.font.color.rgb = RGBColor.from_string(color); p.space_after = Pt(12)
        return tf

    def slide(self, title, eyebrow="LAPORAN PROYEK", notes=""):
        s = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        s.background.fill.solid(); s.background.fill.fore_color.rgb = RGBColor.from_string("F7F9F3")
        self.shape(s,0,0,.16,7.5,self.green)
        self.text(s,eyebrow,.6,.3,12,.3,11,self.green,True)
        self.text(s,title,.6,.85,12,1,30,self.dark,True)
        self.shape(s,.6,6.98,12.1,.012,"CDDAC7")
        self.text(s,"TunasMatch  /  Kelompok 7  /  Machine Learning",.6,7.12,10,.2,10,"607260")
        self.text(s,f"{len(self.prs.slides):02}",12,7.08,.6,.25,12,self.green,True)
        s.notes_slide.notes_text_frame.text = notes
        return s

    def bullets(self, title, lines, notes="", eyebrow="LAPORAN PROYEK"):
        s = self.slide(title,eyebrow,notes)
        for i, line in enumerate(lines):
            self.shape(s,.65,2.02+i*.79,.11,.11,self.gold,MSO_SHAPE.OVAL)
            self.text(s,line,.98,1.9+i*.79,11.6,.73,21)
        return s

    def image(self, title, filename, caption, notes=""):
        s = self.slide(title,notes=notes)
        from PIL import Image as PILImage
        path = ROOT / filename
        with PILImage.open(path) as im: ratio = im.width/im.height
        maxw,maxh = 11.9,4.55
        w,h = min(maxw, maxh*ratio), min(maxh,maxw/ratio)
        s.shapes.add_picture(str(path), Inches((13.333-w)/2), Inches(1.72+(4.55-h)/2), width=Inches(w), height=Inches(h))
        self.text(s,caption,.7,6.35,12,.5,15,"53694E")
        return s

    def table(self, title, headers, rows, caption="", notes="", widths=None):
        s = self.slide(title,notes=notes)
        widths = widths or [12/len(headers)]*len(headers)
        # PowerPoint dapat memperbesar baris ketika teks terlalu banyak. Hitung
        # ruang secara konservatif agar tabel tidak menabrak caption/footer.
        def row_heights(size):
            heights=[]
            for row in [headers]+rows:
                lines=max(sum(max(1,len(textwrap.wrap(part,width=max(7,int((w-.25)*72/(size*.56)))))) for part in str(value).split('\n')) for value,w in zip(row,widths))
                heights.append(max(.47, lines*size*1.24/72+.20))
            return heights
        size=18
        while size>12 and sum(row_heights(size))>4.3:size-=1
        heights=row_heights(size)
        table = s.shapes.add_table(len(rows)+1,len(headers),Inches(.65),Inches(1.95),Inches(12),Inches(sum(heights))).table
        for col,w in zip(table.columns,widths): col.width=Inches(w)
        for row,h in zip(table.rows,heights):row.height=Inches(h)
        for i,row in enumerate([headers]+rows):
            for j,val in enumerate(row):
                c=table.cell(i,j); c.text=str(val); c.margin_left=Inches(.1);c.margin_top=Inches(.12)
                c.fill.solid();c.fill.fore_color.rgb=RGBColor.from_string(self.green if i==0 else ("E7EFDF" if i%2 else "FFFFFF"))
                for p in c.text_frame.paragraphs:
                    p.font.name="Aptos";p.font.size=Pt(size);p.font.bold=i==0
                    p.font.color.rgb=RGBColor.from_string("FFFFFF" if i==0 else self.dark)
        self.text(s,caption,.7,6.4,12,.45,15,"53694E")
        return s


def build_ppt(s, config, cv, test):
    d=Deck(); best=s["selected_model"]
    cover=d.slide("Rekomendasi tanaman,\nberangkat dari kondisi lahan", "TANIPINTAR / KELOMPOK 7", "Judul lengkap di slide dan dokumen. Lengkapi nama/NIM/kelas sebelum pengumpulan. Ini klasifikasi label sumber, bukan jaminan panen.")
    d.text(cover,TITLE,.7,2.35,11.8,1.15,20)
    d.shape(cover,.7,3.85,11.9,.7,"E7EFDF",MSO_SHAPE.ROUNDED_RECTANGLE)
    d.text(cover,"2.200 contoh     /     7 fitur     /     22 tanaman     /     3 model",1,4.02,11,.4,23,d.green,True)
    d.text(cover,f"{config['group_name']} · Kelas {config['class']}\n" + " | ".join(f"{m['name']} ({m['nim']})" for m in config['members']),.7,5.1,11.9,1.3,16)
    d.bullets("Masalah: pilihan tanaman perlu informasi lahan",[
        "Setiap tanaman memiliki kebutuhan hara dan kondisi lingkungan yang berbeda.",
        "Pemilihan tanpa data dapat menambah risiko ketidakcocokan budidaya.",
        "Data tanah dan iklim membuka peluang alat bantu rekomendasi yang terukur.",
        "Ruang lingkup kami: belajar label dataset, bukan mengukur keuntungan/panen."],notes="Latar belakang adalah motivasi, bukan klaim bahwa model telah terbukti mengurangi kerugian petani. Rujukan topik R1 dan R2.")
    d.bullets("Rumusan masalah dan tujuan",[
        "Bagaimana memprediksi label tanaman dari tujuh parameter tanah dan iklim?",
        "Bagaimana performa KNN, Decision Tree dan Logistic Regression dibandingkan?",
        "Kelas apa yang tertukar dan fitur apa yang digunakan kandidat pohon?",
        "Implementasikan model terpilih dalam aplikasi form dan CSV."],notes="Istilah rekomendasi diterapkan pada output klasifikasi multikelas; bukan collaborative filtering.")
    for subset, title in [(REFERENCES[:3],"Studi literatur / 1 dari 2"),(REFERENCES[3:],"Studi literatur / 2 dari 2")]:
        compact={
            'R1': ['Thilakarathne et al.\nKNN, DT, RF, XGB, SVM + cloud','Kaggle; 2.200 contoh; 7 input + label.','RF: accuracy 97,18%; F1 97%; CV 10-fold 97,40%.'],
            'R2': ['Shastri et al.\n10 model + LIME','Kaggle; 2.200 contoh; 22 kelas; split 75:25.','GB: accuracy 99,27%; precision 99,32%; recall 99,36%; F1 99,32%.'],
            'R3': ['Singh & Sharma\nTCRM; pembanding LR/KNN/AdaBoost','3.000 baris menurut artikel; bukan CSV identik proyek.','Accuracy 94%; precision 94,46%; recall 94%; F1 93,97% (abstrak).'],
            'R4': ['Venkateswara & Padmanaban\nTabNet + SHAP','Western Maharashtra; tanaman dan pupuk, bukan dataset identik.','Accuracy tanaman 96,21%; pupuk 95,24% (abstrak).'],
            'R5': ['Dhingra et al.\nLightGBM + SHAP + what-if','7 input; 22 kelas; dashboard Streamlit. Accepted article 2026.','Test accuracy 99,39%; macro-F1 0,9900. Benchmark, bukan bukti lapangan.'],
        }
        rows=[[r['id']+' · '+str(r['year']),*compact[r['id']]] for r in subset]
        d.table(title,["Ref.","Penulis / metode","Dataset / tugas","Hasil utama artikel"],rows,"DOI lengkap di lampiran dan references/. Angka jurnal bukan hasil replikasi proyek.",notes="\n\n".join(f"{r['id']} {r['title']}\nhttps://doi.org/{r['doi']}\nPerbedaan: {r['difference']}\nBukti: {r['evidence']}" for r in subset),widths=[1.1,3.5,3.5,3.9])
    d.bullets("Kontribusi dan perbedaan proyek",[
        "Tiga pendekatan yang mudah dijelaskan; bukan klaim algoritma baru.",
        "Nested CV + GridSearch dengan preprocessing yang aman dari leakage.",
        "Analisis pasangan tanaman tertukar, train–CV–test dan eksperimen scaling.",
        "Streamlit + notebook ber-output + dokumentasi pemula yang konsisten."],notes="R1/R3 lebih menekankan cloud; R2/R5 XAI; R4 tanaman+pupuk dengan data berbeda. Kami tidak menyalin angka, preprocessing atau klaim deployment mereka.")
    d.table("Dataset dan tujuh petunjuk",["Kolom","Arti","Catatan"],[["N, P, K","Nitrogen, fosfor, kalium","Skala sumber; bukan dosis pupuk"],["temperature / humidity","Suhu / kelembapan udara","°C / %; bukan kelembapan tanah"],["ph","Keasaman tanah","Tanpa satuan"],["rainfall","Curah hujan","mm; periode belum terverifikasi"],["label","Target: 22 tanaman","Satu label per contoh"]],"Kaggle — Atharva Ingle. 2.200 baris × 8 kolom. Sumber/hash: data/source_manifest.json.",notes=f"Sumber: {SOURCE_URL}. Baris bukan bukti lahan unik atau kondisi optimal. R1 menjelaskan konteks India dan augmentasi. Lisensi/satuan perlu konfirmasi.")
    d.image("Audit data: kelas seimbang", "plots/distribusi_kelas.png","100 contoh per tanaman · missing 0 · duplikat 0 · tanpa SMOTE",notes="Jangan mengatakan imbalance. Struktur sumber diaudit seluruhnya; EDA fitur menggunakan training.")
    d.image("EDA: outlier tidak langsung dibuang", "plots/kalium_per_kelas.png","K tinggi terkumpul pada apel/anggur dalam sumber; tinjau per kelas sebelum menyebut salah.",notes="Boxplot IQR lengkap dan histogram ada di notebook/plots. Tidak mengklaim semua nilai ekstrem valid secara agronomis; hanya tidak ada dasar menghapus otomatis.")
    d.image("EDA: sebagian kondisi tanaman mirip", "plots/scatter_kemiripan.png","Grafik training. Dua proyeksi membantu interpretasi; model tetap memakai tujuh fitur.",notes="Padi/jute memiliki kemiripan sejumlah NPK/kelembapan. Kacang-kacangan juga dapat bertumpang tindih. Korelasi lengkap ada di lampiran.")
    d.bullets("Preprocessing: cukup yang diperlukan",[
        "Cek skema, angka tidak valid, missing dan duplikat; tidak ada imputasi palsu.",
        "LabelEncoder: nama tanaman ↔ ID 0–21, tanpa makna ordinal.",
        "KNN & LR: StandardScaler → model. Decision Tree tanpa scaler.",
        "Pipeline fit di training/fold saja; test tidak ikut menentukan scaler."],notes="z=(x-mean_train)/std_train. Bukan scaling 0–1, bukan menyamakan satuan biologis, dan tidak menjamin skor naik. Input aplikasi yang kosong ditolak.")
    d.bullets("Training dan validasi tanpa memilih dari test",[
        "Split stratified 80:20, seed 2026: training 1.760 dan test 440.",
        "Nested CV training: outer 5-fold, inner GridSearch 3-fold.",
        "Mean outer macro-F1 memilih keluarga model; lalu final GridSearch 5-fold.",
        "Simpan pilihan dahulu, evaluasi test, lalu simpan model yang sama."],notes="Tiap kelas: 80 train,20 test. Tie: SD terkecil lalu alfabetis. Baseline eksploratif seed42 pernah diperiksa sebelumnya, jadi tidak mengklaim studi blind/preregistered. Tidak mencoba banyak seed atau mengganti pemenang setelah test.")
    d.table("Tiga algoritma, tiga cara membaca pola",["Model","Intuisi","Alasan / batas"],[["KNN","Lihat tetangga kondisi terdekat","Nonlinear; sensitif skala dan k"],["Decision Tree","Pertanyaan ambang bercabang","Aturan/importance terbaca; rentan hafal"],["Logistic Regression","Bobot fitur → skor 22 kelas","Baseline linear; probabilitas belum dikalibrasi"]],"Ketiganya punya predict_proba. Logistic Regression di sini tetap klasifikasi.",notes="KNN dapat memakai distance weights; DT bukan aturan manual. LR memisahkan kelas di ruang tujuh fitur, bukan satu garis untuk semua kelas.")
    tuning=read_json(ROOT / "results/tuning.json")
    d.table("GridSearch dan setelan final",["Model","Ruang pencarian","Terpilih pada training"],[["KNN","k 3/5/7/9/11; uniform/distance; p 1/2",str(tuning["KNN"]["best_params"]).replace("model__","")],["Decision Tree","depth 5/8/12/None; leaf 1/2/4; gini/entropy",str(tuning["Decision Tree"]["best_params"]).replace("model__","")],["Logistic Regression","C 0,01/0,1/1/10/100; max_iter 3000",str(tuning["Logistic Regression"]["best_params"]).replace("model__","")]],"20 / 24 / 5 kombinasi; detail tiap fold dan kandidat tersedia di results/.",notes="Setelan final dicari dari seluruh training. Mean terbaik final grid bukan estimasi utama: untuk perbandingan proses tuning gunakan outer nested CV.")
    d.table("Pemilihan model: hampir seri di validasi",["Model","Outer macro-F1","SD 5 fold","Gap CV train-valid"],[[r.model,f"{r.cv_f1_macro_mean:.6f}",f"{r.cv_f1_macro_std:.6f}",f"{r.cv_gap:.4f}"] for r in cv.itertuples()],f"{best} dipilih menurut aturan mean terbesar; selisih LR–DT amat kecil.",notes="SD bukan confidence interval. Tidak menyatakan LR terbukti signifikan lebih baik. Angka enam desimal sengaja ditampilkan agar aturan pemilihan yang sangat tipis dapat diaudit.")
    d.table("Test akhir: laporkan, jangan pilih ulang",["Model","Accuracy","Precision macro","Recall macro","F1 macro"],[[r.model,*[f"{getattr(r,c):.4f}" for c in ["accuracy","precision_macro","recall_macro","f1_macro"]]] for r in test.itertuples()],"Decision Tree tertinggi di test; model aplikasi tetap pemenang validasi, bukan pemenang test.",notes="440 test =20 per kelas. Ini kesesuaian label sumber, bukan performa dunia nyata. Metrik dan classification report semua 22 kelas ada di notebook/results.")
    d.image("Kesalahan: tanaman mana yang tertukar?", "plots/pasangan_tertukar.png","Rice → jute paling menonjol pada model aktif; kacang-kacangan juga masih tertukar.",notes="Baca arah aktual→prediksi dan jumlah nyata di grafik. Kemiripan pola training adalah hipotesis penjelas, bukan sebab yang telah dibuktikan. Contoh salah dan tujuh nilainya tersedia di test_errors.csv.")
    d.image("Feature importance kandidat Decision Tree", "plots/feature_importance.png","Rainfall, humidity, P berada di posisi atas pada konfigurasi ini.",notes="Impurity importance DT bukan penjelasan lokal model aktif LR, bukan sebab hasil panen dan bukan berarti pH tidak penting secara biologis.")
    d.image("Overfitting: bandingkan metrik yang sama", "plots/train_cv_test.png","Ada gap; train=1 pada KNN distance bukan bukti model selalu benar.",notes="Jarak train-validasi menunjukkan optimisme ringan pada konfigurasi ini. Tidak mengklaim gap kecil membuktikan model memahami hukum pertanian. Tidak terlihat underfitting berat pada kandidat final.")
    d.image("Scaling tidak wajib menaikkan skor", "plots/scaling.png","Ablation: KNN k=5 dan DT depth=8 tetap; memakai CV training, bukan test.",notes="KNN scaled pada setting ini lebih rendah; laporkan jujur. DT sama persis karena transformasi menjaga urutan. DT depth8 belum sekuat final depth12 untuk 22 kelas. Ini ablation, tidak mengubah pemenang setelah test.")
    d.bullets("Implementasi / input → proses → output",[
        "Input: tujuh angka lengkap, atau upload CSV dengan skema yang sama.",
        "Proses: validasi → pipeline terlatih → encoder → nama tanaman.",
        "Output: rekomendasi, tiga skor kelas, grafik dan profil training.",
        "Model/hash sama dengan laporan; input tidak dipakai training ulang."],notes="Min/median/max bukan kondisi ideal. Skor belum dikalibrasi dan bukan peluang panen. Validasi menolak missing/nonnumerik/inf, rentang fisik tidak valid; out-of-range training diperingatkan.")
    screenshot=ROOT / "assets/screenshot_prediksi.png"
    if screenshot.exists(): d.image("Demo aplikasi TaniPintar", "assets/screenshot_prediksi.png", "Jalankan demo nyata: contoh → prediksi → skor → CSV → evaluasi.",notes="Screenshot ini berasal dari aplikasi yang benar-benar dijalankan. Saat presentasi buka aplikasi, bukan hanya gambar. Bahan rekaman video tetap butuh narasi/perkenalan anggota.")
    else: d.bullets("Demo aplikasi / jalankan langsung",["python -m streamlit run app.py","Pilih contoh padi → Muat contoh → Lihat rekomendasi.","Upload examples/contoh_batch.csv; tunjukkan unduh hasil.","Buka Evaluasi model; jelaskan satu kesalahan dan batas skor."],notes="Ganti dengan demo aplikasi langsung; setelah capture_demo.py dan build_materials.py slide ini memakai screenshot nyata.")
    d.bullets("Keterbatasan dan pengembangan",[
        "Konteks India/augmentasi menurut literatur; belum validasi lahan Indonesia.",
        "Satuan NPK/periode hujan dan asal tiap baris belum dapat diaudit.",
        "Tidak ada harga, hama, varietas, lokasi/waktu atau target hasil panen.",
        "Skor belum dikalibrasi; kumpulkan data lokal dan uji eksternal berikutnya."],notes="Kerataan 100/kelas bukan bukti sintetis. R1 menyebut augmentasi; jangan mengarang prosesnya. Split random tidak menilai generalisasi geografis/waktu. Rentang input bukan OOD detector yang andal.")
    d.bullets("Kesimpulan",[
        "Tiga pipeline berhasil mempelajari label tanaman dari tujuh fitur.",
        f"{best} terpilih melalui nested CV, dengan keunggulan LR–DT yang tipis.",
        f"Model aktif benar {int(s['selected_test']['n_correct'])}/440 test; kesalahan per kelas tetap dibahas.",
        "Aplikasi siap dicoba lokal; manfaat budidaya masih memerlukan validasi."],notes="Pisahkan klaim model pada benchmark dari keberhasilan budidaya. Jangan menyebut model paling akurat secara universal.")
    d.table("Pembagian tugas dan tanggung jawab",["Anggota / NIM","Tugas utama"],[[m["name"]+"\n"+m["nim"],m["task"]] for m in config["members"]],"Isi identitas sebenarnya di group_config.json. Semua anggota wajib paham keseluruhan.",notes="Pembagian adalah rancangan, bukan klaim kontribusi telah dikonfirmasi. AI sebagai bantuan belajar/debugging, mahasiswa bertanggung jawab pada kode/analisis.")
    d.image("Lampiran / confusion matrix model aktif", f"plots/confusion_{best.replace(' ', '_')}.png","22 × 22 · baris aktual, kolom prediksi · 20 test per tanaman",notes="Gambar dapat diperbesar pada PPT atau dibuka di plots/. Laporan per kelas lengkap tersedia di results/classification_reports.json.")
    d.image("Lampiran / korelasi antarfitur", "plots/korelasi.png","Korelasi training; target kategori tidak diperlakukan sebagai angka ordinal.")
    d.image("Lampiran / bagian atas pohon", "plots/pohon_ringkas.png","Aturan lengkap: results/aturan_decision_tree.txt; ID kelas: label_mapping.json.")
    d.bullets("Lampiran / daftar pustaka DOI",[f"[{r['id']}] {r['authors'].split(';')[0]} et al. ({r['year']})\nhttps://doi.org/{r['doi']}" for r in REFERENCES],notes="Judul lengkap, jurnal, tabel studi literatur dan bukti verifikasi ada di references/. R5 adalah accepted/early article terbit September2026; jangan mengarang nomor volume.")
    d.prs.save(ROOT / "presentation/Laporan_Proyek_Tanaman.pptx")
    # Dek progress singkat, seperti paket penguin.
    p=Deck()
    p.bullets("TaniPintar / ringkasan progress",["Klasifikasi 22 tanaman dari tujuh parameter tanah dan iklim.","Dataset, EDA, modeling, aplikasi dan materi sudah dibuat.","Identitas, narasi kelompok dan deployment opsional belum final."],eyebrow="PROGRESS / 1")
    p.image("Data dan EDA", "plots/scatter_kemiripan.png","2.200 contoh, seimbang, missing/duplikat 0; sebagian pola bertumpang tindih.")
    p.bullets("Metode dan validasi",["KNN, Decision Tree, Logistic Regression.","Split stratified 80:20; scaler berada di Pipeline.","Nested CV dan GridSearch pada training, test bukan alat pemilihan."])
    p.table("Hasil utama",["Model","CV macro-F1","Test accuracy"],[[r.model,f"{r.cv_f1_macro_mean:.4f}",f"{test.set_index('model').loc[r.model,'accuracy']:.4f}"] for r in cv.itertuples()],f"Aktif: {best}. Keunggulan CV LR–DT sangat tipis.")
    p.image("Analisis kesalahan", "plots/pasangan_tertukar.png","Padi/jute dan beberapa kacang-kacangan menjadi sumber kesalahan.")
    p.bullets("Demo dan langkah kelompok",["Jalankan aplikasi: python -m streamlit run app.py.","Isi nama/NIM/kelas; pahami notebook dan hasil nyata.","Rekam narasi/perkenalan, maksimal7 menit; validasi lapangan belum tersedia."])
    p.prs.save(ROOT / "presentation/Progress_TaniPintar.pptx")


def build_support(s, config, cv, test):
    video = f"""# Naskah video — target 6 menit 40 detik

Rekaman demo_aplikasi.mp4 adalah bahan rekaman layar tanpa suara/perkenalan, bukan video final pengumpulan. Rekam suara dan identitas anggota asli; gabungkan dengan demo. Maksimal 7 menit. Tidak perlu membaca semua slide/lampiran. Gunakan slide utama yang relevan.

## 00:00–00:25 / {config['members'][0]['name']} — perkenalan
Halo, kami {config['group_name']}, kelas {config['class']}: {", ".join(f"{m['name']} ({m['nim']})" for m in config['members'])}. Aplikasi kami bernama {APP_NAME} dengan judul klasifikasi rekomendasi tanaman dari hara tanah dan iklim menggunakan KNN, Decision Tree, dan Logistic Regression.

## 00:25–01:05 / Masalah, tujuan, literatur
Pemilihan tanaman perlu mempertimbangkan lahan. Kami membangun prototipe yang belajar pola tujuh input dan memberi label tanaman. Lima jurnal menjadi dasar: platform cloud, perbandingan supervised, dan interpretabilitas. Kami bukan menciptakan algoritma baru atau membuktikan peningkatan panen.

## 01:05–01:55 / Dataset dan EDA
Ada 2.200 contoh, tujuh fitur, 22 tanaman, masing-masing 100. Jelaskan NPK skala sumber, suhu °C, kelembapan udara %, pH dan hujan mm. Data lengkap, tidak ada duplikat. Tunjukkan distribusi dan scatter. Nilai ekstrem ditinjau per kelas, tidak dihapus otomatis. R1 menyebut konteks India/augmentasi.

## 01:55–02:55 / Anggota 2 — preprocessing dan model
Split stratified 80:20 menjadi 1.760 training dan 440 test. Scaler hanya fit pada training/fold dalam pipeline. KNN bertanya tetangga, DT membuat pertanyaan bercabang, LR belajar bobot/batas linear. Gunakan nested CV outer 5 dan GridSearch inner 3 pada training; final tuning 5 fold. Test tidak dipakai memilih.

## 02:55–03:45 / Evaluasi dan analisis
{s['selected_model']} terpilih dengan nested-CV macro-F1 {s['selected_cv']['cv_f1_macro_mean']:.4f}, hampir seri DT. Pada test, model aktif benar {int(s['selected_test']['n_correct'])}/440. DT mendapat test tertinggi tetapi kami tidak memilih ulang dari test. Tunjukkan satu pasangan rice→jute, importance DT dan gap train-validasi. KNN k=5 scaled tidak lebih tinggi pada ablation; hasil tidak dipaksakan.

## 03:45–05:55 / Anggota 3 — demo aplikasi nyata
Buka Streamlit. Pilih contoh padi, Muat contoh, Lihat rekomendasi. Jelaskan tiga skor bukan peluang panen. Tunjukkan profil training bukan kondisi ideal. Muat satu contoh tanaman lain. Buka tab CSV, upload examples/contoh_batch.csv, proses dan tunjukkan hasil/unduh. Upload contoh_tidak_valid.csv untuk menunjukkan input ditolak. Buka Evaluasi model dan salah satu confusion matrix. Jangan hanya menampilkan screenshot.

## 05:55–06:40 / Kesimpulan, batasan, tugas
Tiga model berhasil mengklasifikasikan label dataset dan aplikasi siap lokal. Data belum divalidasi Indonesia, satuan/periode perlu konfirmasi, tidak ada faktor harga/hama dan probabilitas belum dikalibrasi. Langkah lanjut: data lahan lokal dan validasi eksternal. Sebutkan tugas asli ketiga anggota. Tutup dan pastikan durasi akhir ≤ 7 menit.
"""
    write(ROOT / "video/Naskah_Demo_6_Menit_40_Detik.md", video)
    write(ROOT / "docs/09_Deployment.md", """# Deployment opsional ke Streamlit Community Cloud

Belum ada deployment yang dilakukan atau URL publik yang diklaim. Jangan memakai URL proyek penguin.

1. Pastikan hak berbagi dataset dan model sesuai lisensi sumber. Jangan unggah informasi rahasia atau input pengguna.
2. Buat repository milik kelompok. Unggah app.py, crop_core.py, requirements.txt, .streamlit/config.toml, assets/, Crop_recommendation.csv, models/crop_bundle.joblib, results/, examples/.
3. Hubungkan repository tersebut di Streamlit Community Cloud dan pilih app.py dalam folder proyek.
4. Pilih Python yang didukung beserta paket yang kompatibel. Model dibuat dengan versi sklearn tercatat di results/summary.json; jika environment berbeda, training ulang di environment tujuan dan perbarui hasil/materi, bukan memaksa membuka model tak kompatibel.
5. Jalankan form, CSV, inputinvalid dan halaman evaluasi di aplikasi online. Perubahan lokal tidak otomatis mengubah server; perlu commit/redeploy.
6. Isi deployment_url di group_config.json dan jalankan build_materials.py. Link adalah opsional sesuai ketentuan; aplikasi lokal tetap dapat digunakan untuk demo.

Saat online, input dikirim ke server. Jangan menyatakan semua proses terjadi di browser. Internet lokal hanya diperlukan untuk instalasi/font; font memiliki fallback.
""")
    checklist = [
        ["Pengajuan tema & masalah", "docs/01, PPT Slide 01–03", "Selesai; identitas 3 anggota & kelas terisi"],
        ["Minimal 5 jurnal & tabel", "references/ + PPT Slide 04–05 + Lampiran Word", "Selesai; 5 jurnal nyata ber-DOI + tabel 9 kolom"],
        ["Dataset, sumber, arti variabel", "Crop_recommendation.csv, manifest, docs/02, PPT Slide 06", "Selesai; sumber Kaggle & batasan satuan dijelaskan jujur"],
        ["EDA dan penjelasan visual", "PROJEK_TANAMAN.ipynb, plots/, docs/03, PPT Slide 07–08", "Selesai; seluruh grafik training disertai interpretasi"],
        ["Preprocessing beralasan", "Pipeline di train.py; docs/03, PPT Slide 09", "Selesai; bebas leakage, tanpa SMOTE/imputasi palsu"],
        ["Minimal 3 model", "KNN, DT, LR di train.py, PPT Slide 10–11", "Selesai; dilatih & dituning nyata"],
        ["Training/testing & tuning", "Stratified 80:20, Nested CV, GridSearch", "Selesai; indeks/fold/parameter tersimpan & lulus pytest"],
        ["Evaluasi & analisis", "results/, plots/, docs/05, PPT Slide 12–15", "Selesai; metrik macro, CM 22x22, model terendah, error, overfit, importance"],
        ["Aplikasi input-proses-output", "app.py (TunasMatch), bundle, examples/, PPT Slide 16–17", "Selesai; teruji lokal (pytest + 13 browser checks)"],
        ["Source reproduktif", "PROJEK_TANAMAN.ipynb + scripts + requirements + tests", "Selesai; 20 cell kode tereksekusi tanpa error"],
        ["PPT Laporan Project (A–O)", "presentation/Laporan_Proyek_Tanaman.pptx", "Selesai; 22 slide memakai template ppt pengenalan projek.pptx"],
        ["Portofolio Project CLASS-IPB", "docs/TEK1302_Kelompok7.docx", "Selesai; siap unggah sesuai format KELAS_KELOMPOK"],
        ["Video demo maksimal 7 menit", "video/demo_aplikasi.mp4 + video/Naskah_Demo_6_Menit_40_Detik.md", "Perlu finalisasi narasi & perkenalan 3 anggota"],
        ["Pembagian tugas & pemahaman individu", "group_config.json, docs/08, PPT Slide 20", "Identitas & tugas terisi; siapkan tanya jawab individu"],
    ]
    write(ROOT / "docs/10_Pemetaan_Ketentuan_Project.md", "# Pemetaan ketentuan dan status\n\n" + mdtable(["Ketentuan","Bukti berkas","Status/catatan"],checklist))
    write(ROOT / "MULAI_DI_SINI.md", f"""# Mulai di sini — {APP_NAME}

Kelompok: **{config['group_name']}** | Kelas: **{config['class']}**
Anggota: {", ".join(f"{m['name']} ({m['nim']})" for m in config['members'])}

1. Baca `docs/Penjelasan_Tanaman_Bahasa_Sederhana.docx` untuk pemahaman dari nol.
2. Klik `INSTAL_DEPENDENCY.bat` (sekali), kemudian `JALANKAN_APLIKASI.bat` untuk menjalankan aplikasi **{APP_NAME}**.
3. Buka `PROJEK_TANAMAN.ipynb` untuk kode, penjelasan, dan output lengkap.
4. Buka `presentation/Laporan_Proyek_Tanaman.pptx` untuk PPT Laporan Project final (Bagian A–O, memakai template `ppt pengenalan projek.pptx`).
5. Buka `docs/TEK1302_Kelompok7.docx` untuk berkas unggahan *Portofolio Project* di CLASS-IPB.
6. Baca `references/Daftar_5_Jurnal.md` dan `references/Tabel_Studi_Literatur.csv`.
7. Lengkapi video demo kelompok ≤ 7 menit dengan perkenalan/narasi ketiga anggota; naskah ada di `video/Naskah_Demo_6_Menit_40_Detik.md`.

Model aktif: **{s['selected_model']}**. Dipilih lewat nested CV training; bukan berdasarkan test tertinggi. Test accuracy model aktif **{s['selected_test']['accuracy']:.2%}**. Ini bukan peluang panen berhasil.

Lihat `README.md` untuk build ulang dan `docs/10_Pemetaan_Ketentuan_Project.md` untuk checklist lengkap.
""")
    write(ROOT / "README.md", f"""# {APP_NAME} — Proyek {config['group_name']} ({config['class']})

{TITLE}

**Anggota Kelompok:**
{chr(10).join(f"- {m['name']} (`{m['nim']}`) — {m['task']}" for m in config['members'])}

Paket lokal lengkap: dataset, training, nested CV/tuning, notebook ber-output, model terlatih, aplikasi Streamlit **{APP_NAME}**, PPT Laporan Project (Bagian A–O), dokumen Portofolio CLASS-IPB, buku Word berbahasa sederhana, lima jurnal/tabel studi literatur, skrip uji otomatis, dan bahan demo. Baca `MULAI_DI_SINI.md`.

## Jalankan aplikasi
```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Atau klik `INSTAL_DEPENDENCY.bat` lalu `JALANKAN_APLIKASI.bat`. Aplikasi tidak melakukan training saat startup. Dataset dan model tersedia lokal dengan verifikasi hash SHA-256.

## Hasil nyata
{tables(cv,test)}

**Aktif: {s['selected_model']}**, dipilih dengan mean outer nested-CV macro-F1 tertinggi dan gap train–validasi terkecil (`0.0081`). LR dan DT hampir seri; tidak mengklaim signifikansi statistik. DT tertinggi di test (`0.9864`) dan tidak dipakai mengganti pemenang untuk mencegah selection leakage. Scaling KNN default (`k=5`) tidak memperbaiki skor pada ablation; hasil dilaporkan apa adanya.

## Protokol
Stratified 80:20, seed 2026; training 1.760 / test 440. Nested outer 5-fold + inner GridSearch 3-fold; final GridSearch 5-fold pada training. Scaler berada di dalam `Pipeline`. CV memilih keluarga model sebelum test dibuka; model aplikasi tidak di-refit ke seluruh 2.200 baris. Semua indeks/fold/hasil tersimpan di `results/`.

## Build ulang dan pengujian
```powershell
python -m pip install -r requirements-dev.txt
python train.py
python build_materials.py
python execute_notebook.py
python -m pytest -q
python verify_project.py
```
Notebook menggunakan alur `train.py` yang sama dan folder audit sementara untuk menjaga model utama tetap identik. `build_materials.py` membangun PPT Laporan Project dari template `presentation/ppt pengenalan projek.pptx` melalui `build_ppt_template.py`.

## Struktur
- `app.py` / `crop_core.py`: antarmuka **{APP_NAME}** dan kontrak validasi/inferensi.
- `train.py` / `PROJEK_TANAMAN.ipynb`: eksperimen reproduktif dan notebook ber-output lengkap.
- `models/`: `crop_bundle.joblib` dan tiga pipeline final.
- `results/`: audit data, split, label, seluruh grid, nested folds, prediksi/error, evaluasi per kelas.
- `plots/`: grafik EDA training, korelasi, confusion matrix 22×22, feature importance, scaling, perbandingan.
- `examples/`: template input, contoh batch training, dan contoh input invalid.
- `presentation/Laporan_Proyek_Tanaman.pptx`: PPT Laporan Project final (22 slide, Bagian A–O, memakai template `ppt pengenalan projek.pptx`).
- `docs/TEK1302_Kelompok7.docx`: dokumen siap unggah tugas *Portofolio Project* CLASS-IPB.
- `docs/Penjelasan_Tanaman_Bahasa_Sederhana.docx`: buku penjelasan lengkap berbahasa sederhana.
- `references/`: 5 jurnal nyata, DOI/metadata Crossref, PDF/full-text, dan tabel studi literatur.
- `video/`: naskah demo ≤ 7 menit dan rekaman layar bahan demo.
- `tests/`: pengujian otomatis data/model/inferensi/antarmuka; `verify_project.py` mengaudit paket.

## Batasan dan kejujuran
Sumber yang dirujuk Kaggle Atharva Ingle. R1 menyebut konteks India/augmentasi, tetapi asal tiap baris dan prosedur augmentasi tidak dapat diaudit dari CSV. Satuan NPK dan periode hujan perlu konfirmasi. Label bukan bukti kondisi optimal/hasil panen. Tidak ada validasi eksternal Indonesia; probabilitas belum dikalibrasi. Hasil akurasi bukan janji keuntungan petani.

## Langkah akhir sebelum unggah
- Rekam/tambahkan narasi dan perkenalan ketiga anggota pada video demo (maksimal 7 menit, menampilkan aplikasi {APP_NAME} berjalan langsung).
- Rename folder pengumpulan sesuai format `ML2026_Kelas_NamaKelompok_JudulProject` (contoh: `ML2026_TEK1302_Kelompok7_TunasMatch`).
- Deployment online bersifat opsional (`docs/09_Deployment.md`).

## Environment dan masalah umum
Versi diuji ada di `results/summary.json` dan `requirements*.txt`. Jika port 8501 sibuk: `python -m streamlit run app.py --server.port 8502`.
""")
    deps=["numpy","pandas","scikit-learn","joblib","streamlit"]
    write(ROOT / "requirements.txt", "\n".join(f"{p}=={importlib.metadata.version(p)}" for p in deps))
    dev=["matplotlib","seaborn","python-pptx","python-docx","nbformat","nbclient","ipykernel","pytest","playwright","imageio-ffmpeg","Pillow"]
    write(ROOT / "requirements-dev.txt", "-r requirements.txt\n"+"\n".join(f"{p}=={importlib.metadata.version(p)}" for p in dev))


def main():
    for folder in ["docs","presentation","references","video"]: (ROOT / folder).mkdir(exist_ok=True)
    s=read_json(ROOT / "results/summary.json");config=read_json(ROOT / "group_config.json")
    cv=pd.read_csv(ROOT / "results/cv_comparison.csv");test=pd.read_csv(ROOT / "results/test_comparison.csv")
    build_reference_docs()
    sections=make_sections(s,config,cv,test)
    build_word(sections,config)
    build_portfolio_doc(s,config,cv,test)
    build_notebook()
    build_ppt_from_template(s,config,cv,test)
    build_support(s,config,cv,test)
    print("Materi dibangun dari results/: PPT (template resmi), Word, Portofolio CLASS-IPB, notebook template, docs dan literatur.")


if __name__ == "__main__": main()
