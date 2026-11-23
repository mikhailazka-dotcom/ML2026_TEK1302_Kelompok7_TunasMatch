# 4. Tiga murid, tiga cara belajar

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
