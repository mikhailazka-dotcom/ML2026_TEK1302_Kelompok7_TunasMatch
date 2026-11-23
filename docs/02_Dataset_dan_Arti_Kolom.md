# 2. Isi buku datanya

Data lokal memiliki tepat 2.200 baris, delapan kolom, tujuh input numerik dan satu target kategorikal. Ada 22 tanaman; setiap tanaman memiliki tepat 100 contoh. Tidak ditemukan nilai kosong maupun baris duplikat.

Sumber yang dirujuk adalah Crop Recommendation Dataset oleh Atharva Ingle di Kaggle: https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset. Berkas yang dipakai adalah CSV milik pengguna yang sudah ada di folder, tidak diganti dengan dataset lain. Hash asal ada di data/source_manifest.json.

## Tujuh petunjuk, versi gampang
- N atau nitrogen: unsur hara yang membantu pertumbuhan, termasuk bagian daun.
- P atau fosfor: unsur hara yang berperan dalam energi tanaman serta perkembangan akar dan reproduksi.
- K atau kalium: unsur hara yang membantu pengaturan air dan banyak fungsi tanaman. Analogi 'daya tahan' hanya penyederhanaan.
- Temperature: seberapa panas atau dingin udara, dalam derajat Celsius.
- Humidity: seberapa lembap udara, bukan kadar air tanah, dalam persen.
- pH: ukuran asam atau basa tanah, tanpa satuan. Bukan rasa yang boleh dicicipi; jangan mencicipi tanah.
- Rainfall: besarnya curah hujan, dalam mm. Periode akumulasinya tidak tercantum di CSV, jadi jangan asal menganggap hujan harian, bulanan atau tahunan.

| Kolom | Arti | Satuan/catatan | Rentang sumber |
| --- | --- | --- | --- |
| N | Nitrogen (N) | skala dataset | 0.00–140.00 |
| P | Fosfor (P) | skala dataset | 5.00–145.00 |
| K | Kalium (K) | skala dataset | 5.00–205.00 |
| temperature | Suhu | °C | 8.83–43.68 |
| humidity | Kelembapan udara | % | 14.26–99.98 |
| ph | pH tanah | tanpa satuan | 3.50–9.94 |
| rainfall | Curah hujan | mm; periode perlu dikonfirmasi | 20.21–298.56 |

NPK dibaca sebagai angka kandungan/rasio sesuai skala dataset. Bukan persen komposisi kemasan pupuk dan bukan dosis kg pupuk per hektare. Kita belum memverifikasi satuan laboratoriumnya dari pengelola Kaggle. Jangan mengarang konversi dari sensor atau mg/kg.

## Kenapa datanya disebut seimbang?
Bayangin tiap tanaman kebagian 100 kartu latihan. Tidak ada yang cuma punya dua kartu sementara yang lain punya ribuan. Maka kita tidak memakai SMOTE, oversampling atau class weighting. Tidak semua teknik preprocessing harus dipakai.

## Dari mana konteks India dan augmentasi?
Thilakarathne et al. (2022), bagian 4, mendeskripsikan dataset Kaggle tersebut sebagai augmentasi data hujan, iklim, dan pupuk yang tersedia untuk India [R1]. Ini informasi dari literatur, bukan kesimpulan karena tabelnya rapi. Kita tidak memiliki catatan yang dapat mengaudit proses augmentasi tiap baris. Lisensi sumber juga perlu diperiksa sebelum redistribusi publik.

## Nama 22 tanaman
rice (Padi), maize (Jagung), chickpea (Chickpea (kacang arab)), kidneybeans (Kidney bean (kacang merah)), pigeonpeas (Kacang gude), mothbeans (Moth bean), mungbean (Kacang hijau), blackgram (Black gram), lentil (Lentil), pomegranate (Delima), banana (Pisang), mango (Mangga), grapes (Anggur), watermelon (Semangka), muskmelon (Melon), apple (Apel), orange (Jeruk), papaya (Pepaya), coconut (Kelapa), cotton (Kapas), jute (Jute (serat)), coffee (Kopi).
