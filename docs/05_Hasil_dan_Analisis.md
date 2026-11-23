# 5. Hasil ujian yang benar-benar didapat

| Model | Nested CV F1 ± SD | Test accuracy | Precision macro | Recall macro | F1 macro |
| --- | --- | --- | --- | --- | --- |
| Logistic Regression | 0.9852 ± 0.0042 | 0.9682 | 0.9690 | 0.9682 | 0.9678 |
| Decision Tree | 0.9852 ± 0.0031 | 0.9864 | 0.9869 | 0.9864 | 0.9863 |
| KNN | 0.9824 ± 0.0037 | 0.9705 | 0.9749 | 0.9705 | 0.9699 |

## Siapa yang dipilih?
Model aplikasi adalah Logistic Regression. Pemilihannya mengikuti mean outer nested-CV macro-F1 tertinggi, bukan test accuracy. Mean validasinya 0.985205 dengan SD 0.004202. CV terendah pada konfigurasi ini adalah KNN.

Logistic Regression dan Decision Tree hampir seri. Selisih CV mereka hanya 0.00000221. Ini jauh lebih kecil daripada variasi antarfold, jadi jangan mengatakan LR terbukti unggul secara statistik. Aturan pemilihan yang sudah tetap tetap diikuti; DT adalah alternatif yang layak dipertimbangkan pada penelitian validasi baru.

## Model dengan performa terendah dan kemungkinan penyebabnya
Pada validasi Nested CV, **KNN** memperoleh mean macro-F1 terendah (0.9824 ± 0.0037) dan gap train–validasi terbesar (0.0176). Kemungkinan penyebabnya adalah sifat KNN yang berbasis jarak lokal di ruang 7 fitur sehingga lebih sensitif terhadap tumpang tindih batas kelas antar-tanaman yang kondisinya berdekatan (tercermin pula pada kesalahan uji KNN seperti `rice→jute` 6 kasus dan `mothbeans→lentil` 4 kasus) serta sensitif terhadap pembobotan skala fitur (terlihat pada ablation scaling).

Pada evaluasi holdout test, **Logistic Regression** memperoleh akurasi terendah (0.9682, salah 14/440) dibanding KNN (0.9705) dan Decision Tree (0.9864). Kemungkinan penyebabnya adalah batas keputusan linear Logistic Regression kurang lentur memisahkan sedikit kasus perbatasan non-linear pada pasangan kelas yang sangat mirip (`rice→jute` 5 kasus, `lentil→mothbeans` 3 kasus) dibandingkan pemisahan ambang bercabang milik Decision Tree. Meskipun demikian, Logistic Regression tetap dipertahankan karena dipilih dari validasi sebelum test dibuka.

## Kok test terbaik malah berbeda?
Pada test, Decision Tree mendapat macro-F1 tertinggi, 0.9863. Kita tetap memakai Logistic Regression karena kalau pemenang diganti setelah melihat test, test berubah menjadi alat pemilihan. Model aktif benar pada 426 dari 440 contoh; salah pada 14 contoh. Nilai test ini tidak membuktikan akurasi lapangan Indonesia.

## Cara membaca nilainya
- Accuracy: dari semua soal, berapa bagian yang benar.
- Precision tanaman padi: dari semua yang ditebak padi, berapa yang benar padi.
- Recall padi: dari semua contoh padi asli, berapa yang ditemukan model.
- F1: merangkum keseimbangan precision dan recall.
- Macro: hitung nilai masing-masing tanaman, lalu rata-rata dengan bobot sama.
- Confusion matrix: buku salah tebak. Baris adalah label sebenarnya, kolom adalah tebakan. Nilai diagonal berarti benar.

## Salahnya di mana?
| Aktual | Ditebak menjadi | Jumlah |
| --- | --- | --- |
| rice | jute | 5 |
| lentil | mothbeans | 3 |
| jute | coffee | 1 |
| jute | papaya | 1 |
| jute | rice | 1 |
| mothbeans | lentil | 1 |
| mothbeans | pigeonpeas | 1 |
| pigeonpeas | mango | 1 |

Jumlah di tabel adalah kesalahan pada test model aktif, bukan hasil semua model digabung. Pasangan rice→jute paling menonjol pada model aktif, disusul lentil→mothbeans. Untuk analisis, lihat crop_means_train.csv, scatter_kemiripan.png, dan tujuh nilai tiap contoh salah di test_errors.csv. Padi/jute memiliki beberapa nilai NPK dan kelembapan yang dekat dalam training; hujan membantu membedakan, tetapi sebagian rentang bertumpang tindih. Ini penjelasan masuk akal dari pola data, bukan pembuktian sebab pasti satu prediksi salah.

## Menghafal atau memahami pola?
| Model | F1 train final | F1 nested CV | F1 test | Gap CV train-valid |
| --- | --- | --- | --- | --- |
| Logistic Regression | 0.9926 | 0.9852 | 0.9678 | 0.0081 |
| Decision Tree | 0.9977 | 0.9852 | 0.9863 | 0.0122 |
| KNN | 1.0000 | 0.9824 | 0.9699 | 0.0176 |

KNN dengan pembobotan distance dapat memberi F1 training 1 karena setiap contoh menemukan dirinya sendiri. Nilai itu bukan jaminan generalisasi. Ada gap train-validasi dan train-test; ini indikasi optimisme/overfitting ringan pada konfigurasi yang diuji, bukan diagnosis pasti. Tidak terlihat underfitting berat pada model final karena skor training dan validasi tinggi. Perbedaan final train dengan mean CV tidak identik karena ukuran training dan tuning antarfold berbeda.

## Petunjuk mana yang dipakai pohon?
| Fitur | Importance DT |
| --- | --- |
| rainfall | 0.3683 |
| humidity | 0.2239 |
| P | 0.2103 |
| K | 0.0938 |
| temperature | 0.0503 |
| N | 0.0463 |
| ph | 0.0071 |

Tiga teratas adalah rainfall, humidity, P. Ini impurity importance milik Decision Tree, bukan penjelasan lokal mengapa Logistic Regression memilih satu tanaman. Importance tidak membuktikan penyebab hasil panen, dapat dipengaruhi korelasi dan metode perhitungan. pH rendah importance bukan berarti pH tidak penting secara biologis.

## Scaling: hasilnya boleh tidak sesuai dugaan
| Model | Pakai scaling? | Mean CV F1 | Setelan tetap |
| --- | --- | --- | --- |
| KNN | False | 0.9785 | k=5 |
| KNN | True | 0.9714 | k=5 |
| Decision Tree | False | 0.8045 | max_depth=8 |
| Decision Tree | True | 0.8045 | max_depth=8 |

Pada KNN k=5 default, scaling justru menurunkan mean CV pada split ini. Artinya bobot implisit jarak mentah kebetulan lebih membantu konfigurasi ini; bukan bukti bahwa scaling selalu buruk. KNN final dituning di ruang scaled sesuai rancangan, sedangkan KNN unscaled hanya ablation CV dan tidak dipakai memilih ulang setelah test. DT menghasilkan skor sama pada ablation scaling; pohon depth=8 jauh lebih dangkal daripada konfigurasi final depth=12 sehingga skornya lebih rendah. Jangan membandingkan angka ablation depth=8 dengan hasil tuning final seolah modelnya sama.
