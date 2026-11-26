# TunasMatch — Proyek Kelompok 7 (TEK1302|Pembelajaran Mesin)

Klasifikasi Rekomendasi Jenis Tanaman Berdasarkan Kandungan Hara Tanah dan Kondisi Iklim Menggunakan K-Nearest Neighbors, Decision Tree, dan Logistic Regression

**Anggota Kelompok:**
- Azaria Nur Febriasari (`J0404241041`) — Dataset, EDA, Preprocessing, dan Studi Literatur
- Radinal Avram Utama (`J0404241161`) — Pengembangan Model, Tuning, Nested CV, dan Evaluasi
- Mikhail Rafi Azka (`J0404241168`) — Implementasi Aplikasi TunasMatch, Dokumentasi, dan Video Demo

## Tautan Penting
- **Aplikasi Web Online (TunasMatch):** https://ml2026tek1302kelompok7tunasmatch.streamlit.app
- **Repository GitHub:** https://github.com/mikhailazka-dotcom/ML2026_TEK1302_Kelompok7_TunasMatch
- **Dataset Sumber:** https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset

Paket lokal lengkap: dataset, training, nested CV/tuning, notebook ber-output, model terlatih, aplikasi Streamlit **TunasMatch**, skrip uji otomatis, dan bahan demo. Baca `MULAI_DI_SINI.md`.

## Jalankan aplikasi
```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Atau klik `INSTAL_DEPENDENCY.bat` lalu `JALANKAN_APLIKASI.bat`. Aplikasi tidak melakukan training saat startup. Dataset dan model tersedia lokal dengan verifikasi hash SHA-256.

## Hasil nyata
| Model | Nested CV F1 ± SD | Test accuracy | Precision macro | Recall macro | F1 macro |
| --- | --- | --- | --- | --- | --- |
| Logistic Regression | 0.9852 ± 0.0042 | 0.9682 | 0.9690 | 0.9682 | 0.9678 |
| Decision Tree | 0.9852 ± 0.0031 | 0.9864 | 0.9869 | 0.9864 | 0.9863 |
| KNN | 0.9824 ± 0.0037 | 0.9705 | 0.9749 | 0.9705 | 0.9699 |

**Aktif: Logistic Regression**, dipilih dengan mean outer nested-CV macro-F1 tertinggi dan gap train–validasi terkecil (`0.0081`). LR dan DT hampir seri; tidak mengklaim signifikansi statistik. DT tertinggi di test (`0.9864`) dan tidak dipakai mengganti pemenang untuk mencegah selection leakage. Scaling KNN default (`k=5`) tidak memperbaiki skor pada ablation; hasil dilaporkan apa adanya.

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
- `app.py` / `crop_core.py`: antarmuka **TunasMatch** dan kontrak validasi/inferensi.
- `train.py` / `PROJEK_TANAMAN.ipynb`: eksperimen reproduktif dan notebook ber-output lengkap.
- `models/`: `crop_bundle.joblib` dan tiga pipeline final.
- `results/`: audit data, split, label, seluruh grid, nested folds, prediksi/error, evaluasi per kelas.
- `plots/`: grafik EDA training, korelasi, confusion matrix 22×22, feature importance, scaling, perbandingan.
- `examples/`: template input, contoh batch training, dan contoh input invalid.
- `tests/`: pengujian otomatis data/model/inferensi/antarmuka; `verify_project.py` mengaudit paket.

## Batasan dan kejujuran
Sumber yang dirujuk Kaggle Atharva Ingle. R1 menyebut konteks India/augmentasi, tetapi asal tiap baris dan prosedur augmentasi tidak dapat diaudit dari CSV. Satuan NPK dan periode hujan perlu konfirmasi. Label bukan bukti kondisi optimal/hasil panen. Tidak ada validasi eksternal Indonesia; probabilitas belum dikalibrasi. Hasil akurasi bukan janji keuntungan petani.

## Environment dan masalah umum
Versi diuji ada di `results/summary.json` dan `requirements*.txt`. Jika port 8501 sibuk: `python -m streamlit run app.py --server.port 8502`.
