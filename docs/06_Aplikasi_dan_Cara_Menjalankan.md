# 6. Dari buku latihan menjadi aplikasi

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

Kode tidak menyimpan input pengguna secara permanen. Jika aplikasi di-deploy online, data tetap dikirim ke server untuk diproses. Belum ada sistem akun, monitoring agronomis atau IoT. Link deployment: https://ml2026tek1302kelompok7tunasmatch.streamlit.app

## Membuat ulang proyek
Pasang requirements-dev.txt. Jalankan python train.py; python build_materials.py; python execute_notebook.py; python -m pytest -q; python capture_demo.py; lalu python build_materials.py untuk menyisipkan screenshot terbaru. Notebook mengeksekusi training ke folder audit sementara, tidak menimpa model utama. Perubahan dependency sklearn memerlukan training ulang dan pengujian ulang.
