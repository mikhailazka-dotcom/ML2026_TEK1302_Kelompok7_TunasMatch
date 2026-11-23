# 1. Sebenarnya kita sedang bikin apa?

Bayangin kamu punya buku latihan. Di setiap baris ada tujuh petunjuk kondisi tanah dan cuaca, lalu ada nama tanaman. Kita mengajari komputer membaca hubungan petunjuk dengan nama tanaman itu.

Kalimat paling gampang: **angka kondisi lahan masuk, tebakan nama tanaman keluar**. Kita tidak mengolah foto daun, tidak meramal harga, tidak menghitung ton panen, dan tidak menentukan berapa karung pupuk yang harus dibeli.

Nama aplikasi kita TunasMatch. Judul akademiknya: Klasifikasi Rekomendasi Jenis Tanaman Berdasarkan Kandungan Hara Tanah dan Kondisi Iklim Menggunakan K-Nearest Neighbors, Decision Tree, dan Logistic Regression.

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
