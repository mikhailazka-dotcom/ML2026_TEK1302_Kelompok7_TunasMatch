# Naskah Video Demo Aplikasi — TunasMatch (Target: 6 Menit 30 Detik | Maksimal 7 Menit)

**Identitas Kelompok**
- **Kelompok:** Kelompok 7 — Kelas `TEK1302 | Pembelajaran Mesin`
- **Program Studi / Institusi:** Teknologi Rekayasa Komputer, Sekolah Vokasi IPB University
- **Anggota:**
  1. **Azaria Nur Febriasari** (`J0404241041`) — Dataset, EDA, Preprocessing, & Studi Literatur
  2. **Radinal Avram Utama** (`J0404241161`) — Pengembangan Model, Tuning, Nested CV, & Evaluasi
  3. **Mikhail Rafi Azka** (`J0404241168`) — Implementasi Aplikasi TunasMatch, Dokumentasi, & Demo
- **Judul Project:** *Klasifikasi Rekomendasi Jenis Tanaman Berdasarkan Kandungan Hara Tanah dan Kondisi Iklim Menggunakan K-Nearest Neighbors, Decision Tree, dan Logistic Regression*
- **Aplikasi:** **TunasMatch** (`https://ml2026tek1302kelompok7tunasmatch.streamlit.app` atau lokal `streamlit run app.py`)
- **Repositori:** `https://github.com/mikhailazka-dotcom/ML2026_TEK1302_Kelompok7_TunasMatch`

> **Tips Rekaman agar Pas ≤ 7 Menit:**
> - Bicara dengan tempo santai dan jelas (~135 kata/menit). Total narasi naskah ini sekitar **850 kata**, sehingga dengan jeda klik demo langsung akan selesai di kisaran **6 menit 15 detik – 6 menit 45 detik**.
> - Sebelum mulai merekam, **buka lebih dulu** aplikasi TunasMatch di browser (pastikan tidak sedang *sleep* jika memakai link Streamlit Cloud, atau jalankan `JALANKAN_APLIKASI.bat` secara lokal) dan siapkan file `examples/contoh_batch.csv` serta `examples/contoh_tidak_valid.csv` agar mudah dipilih saat upload.
> - Aplikasi **wajib dijalankan langsung** saat demonstrasi (bukan menampilkan screenshot).

---

## Ringkasan Pembagian Waktu

| Waktu | Durasi | Pembicara | Segmen & Cakupan Wajib |
| :--- | :--- | :--- | :--- |
| **00:00 – 00:35** | 35 dtk | **Azaria** (sapa bertiga) | Perkenalan anggota & judul project |
| **00:35 – 01:10** | 35 dtk | **Azaria** | Latar belakang masalah & ringkasan 5 jurnal |
| **01:10 – 01:55** | 45 dtk | **Azaria** | Dataset & Exploratory Data Analysis (EDA) |
| **01:55 – 02:50** | 55 dtk | **Radinal** | Preprocessing bebas kebocoran & 3 algoritma ML |
| **02:50 – 03:45** | 55 dtk | **Radinal** | Perbandingan model, model terpilih, & analisis kesalahan |
| **03:45 – 05:50** | 2 mnt 05 dtk | **Mikhail** | Demonstrasi live aplikasi **TunasMatch** |
| **05:50 – 06:30** | 40 dtk | **Mikhail** (tutup bertiga) | Kesimpulan, keterbatasan, pembagian tugas, & penutup |

---

## Segmen 1 — Perkenalan & Judul Project (`00:00 – 00:35`)
**Pembicara:** Azaria Nur Febriasari (disertai sapaan singkat Radinal & Mikhail)  
**[LAYAR / AKSI]:** Tampilkan **Slide 1 (Judul Project & Identitas Kelompok)** dari `Laporan_Proyek_Tanaman.pptx`. Aktifkan kamera ketiga anggota jika merekam via Zoom/OBS.

**[NARASI — Azaria]:**
> "Halo semuanya, selamat pagi/siang. Kami dari Kelompok 7, kelas TEK1302 Pembelajaran Mesin, Program Studi Teknologi Rekayasa Komputer, Sekolah Vokasi IPB University.  
> Perkenalkan, saya **Azaria Nur Febriasari** dengan NIM J0404241041..."

**[NARASI — Radinal]:**
> "...saya **Radinal Avram Utama**, NIM J0404241161..."

**[NARASI — Mikhail]:**
> "...dan saya **Mikhail Rafi Azka**, NIM J0404241168."

**[NARASI — Azaria]:**
> "Hari ini kami akan mempresentasikan project akhir kami berjudul **Klasifikasi Rekomendasi Jenis Tanaman Berdasarkan Kandungan Hara Tanah dan Kondisi Iklim Menggunakan K-Nearest Neighbors, Decision Tree, dan Logistic Regression**, yang kami wujudkan dalam aplikasi bernama **TunasMatch**."

---

## Segmen 2 — Latar Belakang Masalah & Studi Literatur (`00:35 – 01:10`)
**Pembicara:** Azaria Nur Febriasari  
**[LAYAR / AKSI]:** Pindah ke **Slide Latar Belakang & Tujuan**, lalu tampilkan singkat **Slide Tabel Studi Literatur (5 Jurnal)**.

**[NARASI — Azaria]:**
> "Di bidang pertanian, memilih jenis tanaman yang cocok dengan kondisi lahan tidak mudah karena banyak faktor bekerja bersamaan—mulai dari hara tanah seperti nitrogen, fosfor, dan kalium, hingga suhu, kelembapan, pH, dan curah hujan. Keputusan yang hanya mengandalkan perkiraan umum berisiko kurang sesuai dengan kondisi lahan.  
> Berdasarkan lima jurnal ilmiah referensi—mulai dari Thilakarathne, Shastri, Singh, Venkateswara, hingga KRISHI.AI—pendekatan *machine learning* banyak dipakai untuk rekomendasi tanaman. Namun, fokus project kami bukan membuat algoritma baru atau menjanjikan peningkatan panen, melainkan membandingkan tiga algoritma klasik secara transparan, bebas kebocoran data uji, lengkap dengan analisis kesalahan per kelas dan aplikasi yang bisa langsung dicoba."

---

## Segmen 3 — Dataset & Eksplorasi Data / EDA (`01:10 – 01:55`)
**Pembicara:** Azaria Nur Febriasari  
**[LAYAR / AKSI]:** Tampilkan **Slide Dataset** dan **Slide EDA** (grafik distribusi kelas, boxplot/kalium per kelas, korelasi, dan scatter tumpang tindih).

**[NARASI — Azaria]:**
> "Kami menggunakan **Crop Recommendation Dataset** dari Kaggle oleh Atharva Ingle, dengan total **2.200 baris data**, **tujuh fitur numerik**—yaitu N, P, K pada skala dataset, suhu dalam derajat Celsius, kelembapan udara dalam persen, pH tanah, dan curah hujan dalam milimeter—serta **22 kelas tanaman** yang seimbang sempurna, masing-masing 100 data.  
> Hasil audit kualitas menunjukkan **nol missing value** dan **nol duplikat**. Dari EDA pada data latih, korelasi tertinggi ada pada fosfor dan kalium sebesar 0,737. Memang terdapat nilai ekstrem saat dicek dengan IQR, misalnya kalium tinggi pada apel dan anggur, sehingga outlier **tidak kami hapus otomatis** karena merupakan ciri alami tanaman tersebut. Selain itu, grafik *scatter* memperlihatkan tumpang tindih antara padi dan jute, serta antar kacang-kacangan seperti lentil dan mothbeans. Catatan pentingnya, literatur menyebut dataset ini berkonteks India dan melalui augmentasi, sehingga belum divalidasi pada lahan Indonesia. Selanjutnya, tahap preprocessing dan pemodelan akan dijelaskan oleh Radinal."

---

## Segmen 4 — Preprocessing & Algoritma Machine Learning (`01:55 – 02:50`)
**Pembicara:** Radinal Avram Utama  
**[LAYAR / AKSI]:** Tampilkan **Slide Preprocessing** dan **Slide Pengembangan Model** (alur split 80:20, Pipeline, dan 3 algoritma).

**[NARASI — Radinal]:**
> "Terima kasih, Azaria. Pada tahap preprocessing, langkah pertama kami membagi dataset secara **stratified 80 banding 20** dengan *random seed* 2026 menjadi **1.760 data latih** dan **440 data uji**. Data uji langsung kami kunci dan tidak pernah disentuh saat eksplorasi lanjutan, scaling, maupun pemilihan model.  
> Karena data sudah lengkap dan seimbang, kami tidak melakukan imputasi buatan maupun SMOTE. Label 22 tanaman dikodekan memakai `LabelEncoder`, lalu kami membungkus `StandardScaler` di dalam `Pipeline` khusus untuk KNN dan Logistic Regression agar parameter rata-rata dan standar deviasi hanya dipelajari dari data latih. Decision Tree tidak memerlukan scaling karena berbasis ambang batas.  
> Kami membandingkan tiga algoritma dengan cara belajar berbeda: **K-Nearest Neighbors** berbasis kemiripan jarak, **Decision Tree** berbasis aturan bercabang, dan **Logistic Regression** berbasis batas linear multikelas. Untuk menyetel hyperparameter sekaligus memilih model secara objektif, kami menerapkan **Nested Cross-Validation** pada data latih saja—yaitu 5 *outer fold* dan *GridSearch* 3 *inner fold* dengan metrik utama **macro-F1**."

---

## Segmen 5 — Perbandingan Performa, Model Terbaik, & Analisis (`02:50 – 03:45`)
**Pembicara:** Radinal Avram Utama  
**[LAYAR / AKSI]:** Tampilkan **Slide Evaluasi & Perbandingan Model**, **Slide Pemilihan Model Terbaik**, lalu **Slide Confusion Matrix & Analisis Kesalahan**.

**[NARASI — Radinal]:**
> "Ini adalah hasil eksperimen kami. Pada **Nested Cross-Validation** data latih, ketiga model meraih macro-F1 di atas 0,98: **Logistic Regression** 0,985205, **Decision Tree** 0,985203, dan **KNN** 0,9824. Selisih Logistic Regression dan Decision Tree sangat tipis dan tidak diklaim signifikan secara statistik, namun sesuai aturan yang ditetapkan sebelum data uji dibuka—mean outer macro-F1 terbesar—**Logistic Regression** terpilih sebagai model aktif, sekaligus memiliki *gap* latih–validasi terkecil, yaitu 0,0081.  
> Saat dievaluasi sekali pada 440 data uji, **Decision Tree** memang meraih akurasi tertinggi 98,64% atau 434 benar, diikuti **KNN** 97,05%, dan **Logistic Regression** 96,82% atau 426 benar. Kami **sengaja tidak mengganti pemenang ke Decision Tree** setelah melihat data uji, karena mengganti model berdasarkan skor *test* akan menyebabkan kebocoran seleksi.  
> Dari *confusion matrix*, 14 kesalahan Logistic Regression terkonsentrasi pada pasangan yang memang bertumpang tindih secara fitur, terutama **padi diprediksi sebagai jute** sebanyak 5 kasus dan **lentil sebagai mothbeans** 3 kasus. Menariknya, pada uji ablasi scaling, KNN dengan k=5 justru sedikit lebih baik tanpa scaling, dan hasil itu kami laporkan apa adanya. Selanjutnya, Mikhail akan mendemonstrasikan aplikasi TunasMatch secara langsung."

---

## Segmen 6 — Demonstrasi Live Aplikasi TunasMatch (`03:45 – 05:50`)
**Pembicara:** Mikhail Rafi Azka  
**[LAYAR / AKSI]:** **Pindah ke browser yang menjalankan aplikasi TunasMatch secara langsung** (Streamlit Cloud atau lokal). Pastikan gerakan kursor tenang dan jelas.

### 6A. Prediksi Satu Lahan (`03:45 – 04:40`)
**[AKSI]:** Di halaman **Rekomendasi → tab Satu lahan**, klik dropdown contoh tanaman (Padi), klik **Muat contoh**, lalu klik tombol hijau **Lihat rekomendasi**. Tunjukkan kartu hasil, tiga skor teratas, kotak peringatan kuning, dan tabel profil training.

**[NARASI — Mikhail]:**
> "Terima kasih, Radinal. Sekarang kita masuk ke demonstrasi langsung aplikasi **TunasMatch** yang dibangun dengan Streamlit dan memuat model Logistic Regression terlatih dari bundel `joblib` berverifikasi hash SHA-256—tanpa melatih ulang saat aplikasi dibuka.  
> Pertama, kita coba tab **Satu lahan**. Di sini pengguna bisa mengisi tujuh parameter lahan secara manual atau memuat contoh data training untuk uji coba. Saya muat contoh **Padi**, lalu klik **Lihat rekomendasi**.  
> Di sisi kanan langsung muncul rekomendasi utama **Padi** beserta **tiga skor kelas teratas**—Padi, Jute, dan Kacang gude. Kami menampilkan peringatan tegas bahwa skor ini adalah keluaran probabilitas model yang **belum dikalibrasi**, bukan peluang keberhasilan panen. Di bawahnya juga tersedia tabel rentang minimum, median, dan maksimum dari data training sebagai pembanding, serta tombol unduh hasil CSV."

**[AKSI]:** Ubah salah satu input (misal ubah `Curah hujan` atau pilih contoh lain seperti **Apel** → **Muat contoh** → **Lihat rekomendasi**, atau masukkan angka ekstrem misal `N = 300`) agar terlihat perubahan hasil / peringatan di luar rentang training.

**[NARASI — Mikhail]:**
> "Jika kita ganti ke contoh tanaman lain, misalnya **Apel**, dan klik **Lihat rekomendasi**, hasil dan profilnya langsung diperbarui. Apabila pengguna memasukkan nilai di luar rentang data training, aplikasi tetap memproses namun memunculkan peringatan bahwa prediksi kurang didukung data."

### 6B. Prediksi Banyak Lahan / Batch CSV & Validasi Input (`04:40 – 05:25`)
**[AKSI]:** Klik tab **Banyak lahan / CSV**. Upload `examples/contoh_batch.csv` → tunggu preview tabel muncul → klik **Proses CSV** → scroll singkat hasil 22 baris dan tunjukkan tombol **Unduh hasil batch**. Lalu upload `examples/contoh_tidak_valid.csv` (humidity = 120) untuk menunjukkan pesan error validasi.

**[NARASI — Mikhail]:**
> "Berikutnya, pada tab **Banyak lahan / CSV**, pengguna bisa mengunggah hingga 10.000 baris data sekaligus. Saya unggah file `contoh_batch.csv` berisi 22 contoh lahan, lalu klik **Proses CSV**. Dalam sekejap, seluruh baris selesai diprediksi lengkap dengan nama tanaman, tiga skor teratas, dan siap diunduh sebagai CSV.  
> Untuk menjaga keandalan, aplikasi juga memiliki validasi ketat. Jika saya unggah `contoh_tidak_valid.csv` yang memiliki nilai kelembapan 120 persen, aplikasi langsung menolak dengan pesan kesalahan yang jelas, alih-alih memaksakan prediksi yang menyesatkan."

### 6C. Halaman Evaluasi Model & Kenali Dataset (`05:25 – 05:50`)
**[AKSI]:** Klik menu sidebar **Evaluasi model** → tunjukkan tabel Nested CV & Test → klik tab **Kesalahan prediksi** (tunjukkan confusion matrix 22×22) → klik cepat menu **Kenali dataset**.

**[NARASI — Mikhail]:**
> "Selain prediksi, pengguna dapat meninjau transparansi model pada menu **Evaluasi model**—mulai dari perbandingan Nested CV, hasil test, *confusion matrix* interaktif untuk ketiga model, *feature importance* Decision Tree, hingga uji ablasi scaling. Di menu **Kenali dataset** dan **Panduan**, tersedia pula penjelasan arti kolom serta batasan sistem."

---

## Segmen 7 — Kesimpulan, Keterbatasan, Pembagian Tugas, & Penutup (`05:50 – 06:30`)
**Pembicara:** Mikhail Rafi Azka (penutup bersama)  
**[LAYAR / AKSI]:** Pindah ke **Slide Kesimpulan, Keterbatasan, & Pembagian Tugas**.

**[NARASI — Mikhail]:**
> "Sebagai kesimpulan, ketiga algoritma berhasil mencapai macro-F1 validasi di atas 0,98, dan **Logistic Regression** terpilih melalui protokol *nested cross-validation* bebas kebocoran data uji dengan akurasi test 96,82%, lalu berhasil diimplementasikan dalam aplikasi web **TunasMatch** yang dapat diakses lokal maupun daring.  
> Kami menyadari keterbatasan project ini: dataset belum divalidasi pada lahan nyata Indonesia, belum mencakup faktor varietas, hama, irigasi, atau harga pasar, serta probabilitas model belum dikalibrasi. Ke depannya, pengembangan dapat diarahkan pada pengumpulan data lokal ber-ID lahan dan musim, kalibrasi probabilitas, serta penerapan *explainable AI* seperti SHAP bersama pakar agronomi.  
> Dalam pengerjaannya, **Azaria** menangani dataset, EDA, preprocessing, dan studi literatur; **Radinal** menangani pemodelan, tuning, nested CV, dan evaluasi; serta **saya (Mikhail)** menangani aplikasi TunasMatch, dokumentasi, dan demo—dengan seluruh anggota memahami keseluruhan proses project.  
> Sekian demonstrasi dari Kelompok 7. Terima kasih atas perhatiannya, sampai jumpa!"

---

## Checklist Cepat Sebelum Mengunggah Video
- [ ] Total durasi video **≤ 07:00** (target aman 06:15–06:45).
- [ ] Semua 3 anggota tampil/bersuara memperkenalkan nama dan NIM masing-masing.
- [ ] Aplikasi **TunasMatch** benar-benar dijalankan langsung (klik *Muat contoh*, *Lihat rekomendasi*, upload `contoh_batch.csv`, upload `contoh_tidak_valid.csv`, buka *Evaluasi model*).
- [ ] Audio jelas dan tidak tertutup suara latar.
- [ ] Nama folder pengumpulan disesuaikan dengan format `ML2026_Kelas_NamaKelompok_JudulProject` (contoh: `ML2026_TEK1302_Kelompok7_TunasMatch`).
