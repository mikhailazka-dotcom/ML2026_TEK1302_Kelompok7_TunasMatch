# Naskah video — target 6 menit 40 detik

Rekaman demo_aplikasi.mp4 adalah bahan rekaman layar tanpa suara/perkenalan, bukan video final pengumpulan. Rekam suara dan identitas anggota asli; gabungkan dengan demo. Maksimal 7 menit. Tidak perlu membaca semua slide/lampiran. Gunakan slide utama yang relevan.

## 00:00–00:25 / Azaria Nur Febriasari — perkenalan
Halo, kami Kelompok 7, kelas TEK1302|Pembelajaran Mesin: Azaria Nur Febriasari (J0404241041), Radinal Avram Utama (J0404241161), Mikhail Rafi Azka (J0404241168). Aplikasi kami bernama TunasMatch dengan judul klasifikasi rekomendasi tanaman dari hara tanah dan iklim menggunakan KNN, Decision Tree, dan Logistic Regression.

## 00:25–01:05 / Masalah, tujuan, literatur
Pemilihan tanaman perlu mempertimbangkan lahan. Kami membangun prototipe yang belajar pola tujuh input dan memberi label tanaman. Lima jurnal menjadi dasar: platform cloud, perbandingan supervised, dan interpretabilitas. Kami bukan menciptakan algoritma baru atau membuktikan peningkatan panen.

## 01:05–01:55 / Dataset dan EDA
Ada 2.200 contoh, tujuh fitur, 22 tanaman, masing-masing 100. Jelaskan NPK skala sumber, suhu °C, kelembapan udara %, pH dan hujan mm. Data lengkap, tidak ada duplikat. Tunjukkan distribusi dan scatter. Nilai ekstrem ditinjau per kelas, tidak dihapus otomatis. R1 menyebut konteks India/augmentasi.

## 01:55–02:55 / Anggota 2 — preprocessing dan model
Split stratified 80:20 menjadi 1.760 training dan 440 test. Scaler hanya fit pada training/fold dalam pipeline. KNN bertanya tetangga, DT membuat pertanyaan bercabang, LR belajar bobot/batas linear. Gunakan nested CV outer 5 dan GridSearch inner 3 pada training; final tuning 5 fold. Test tidak dipakai memilih.

## 02:55–03:45 / Evaluasi dan analisis
Logistic Regression terpilih dengan nested-CV macro-F1 0.9852, hampir seri DT. Pada test, model aktif benar 426/440. DT mendapat test tertinggi tetapi kami tidak memilih ulang dari test. Tunjukkan satu pasangan rice→jute, importance DT dan gap train-validasi. KNN k=5 scaled tidak lebih tinggi pada ablation; hasil tidak dipaksakan.

## 03:45–05:55 / Anggota 3 — demo aplikasi nyata
Buka Streamlit. Pilih contoh padi, Muat contoh, Lihat rekomendasi. Jelaskan tiga skor bukan peluang panen. Tunjukkan profil training bukan kondisi ideal. Muat satu contoh tanaman lain. Buka tab CSV, upload examples/contoh_batch.csv, proses dan tunjukkan hasil/unduh. Upload contoh_tidak_valid.csv untuk menunjukkan input ditolak. Buka Evaluasi model dan salah satu confusion matrix. Jangan hanya menampilkan screenshot.

## 05:55–06:40 / Kesimpulan, batasan, tugas
Tiga model berhasil mengklasifikasikan label dataset dan aplikasi siap lokal. Data belum divalidasi Indonesia, satuan/periode perlu konfirmasi, tidak ada faktor harga/hama dan probabilitas belum dikalibrasi. Langkah lanjut: data lahan lokal dan validasi eksternal. Sebutkan tugas asli ketiga anggota. Tutup dan pastikan durasi akhir ≤ 7 menit.
