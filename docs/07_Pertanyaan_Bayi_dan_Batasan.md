# 7. Pertanyaan yang biasanya bikin bingung

## Jadi gua mengolah apa?
Kamu mengolah tabel contoh hubungan tujuh kondisi tanah/iklim dengan nama tanaman. Kamu mengecek kualitasnya, memahami pola, melatih tiga model, membandingkan kemampuan menebak label pada contoh yang tidak dilatih, lalu membuat aplikasi untuk memakai model terpilih.

## Kenapa bukan langsung cari tanaman dengan rata-rata paling dekat?
Itu bisa dijadikan baseline lain. Tiga model kita mempelajari batas atau kemiripan dengan cara berbeda; tidak hanya membandingkan satu rata-rata. Kita menguji mana yang bekerja pada prosedur yang sama, bukan menganggap satu cara selalu benar.

## Apakah 98% berarti petani pasti untung?
Tidak. Accuracy hanya menghitung kesesuaian tebakan dengan label sumber. Tidak ada data keuntungan atau hasil panen di CSV. Model bisa mendapat skor tinggi pada tabel tetapi gagal pada pengukuran lapangan yang definisinya berbeda.

## Kenapa Decision Tree tidak dipakai padahal test-nya bagus?
Karena pemilihan dilakukan di latihan validasi, sebelum membuka ujian akhir. Dalam eksperimen ini Logistic Regression menang sangat tipis di validasi. Mengganti pemenang setelah melihat test berarti memakai kunci ujian untuk memilih. Bila ingin mengubah aturan pemilihan, lakukan penelitian baru dengan evaluasi eksternal baru, bukan mengklaim holdout lama tetap independen.

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
Kita mengajari tiga murid membaca tujuh petunjuk untuk menebak satu dari 22 tanaman. Mereka latihan dari 1.760 contoh, diadu dengan nested CV, lalu diuji pada 440 contoh. Logistic Regression dipakai dalam aplikasi sesuai aturan validasi. Ini alat belajar pola data, bukan mesin penjamin panen.
