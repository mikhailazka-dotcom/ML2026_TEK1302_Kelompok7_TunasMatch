# 3. Mengolahnya ngapain aja?

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
