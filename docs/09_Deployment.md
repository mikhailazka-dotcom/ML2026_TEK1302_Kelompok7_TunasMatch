# Deployment opsional ke Streamlit Community Cloud

Belum ada deployment yang dilakukan atau URL publik yang diklaim. Jangan memakai URL proyek penguin.

1. Pastikan hak berbagi dataset dan model sesuai lisensi sumber. Jangan unggah informasi rahasia atau input pengguna.
2. Buat repository milik kelompok. Unggah app.py, crop_core.py, requirements.txt, .streamlit/config.toml, assets/, Crop_recommendation.csv, models/crop_bundle.joblib, results/, examples/.
3. Hubungkan repository tersebut di Streamlit Community Cloud dan pilih app.py dalam folder proyek.
4. Pilih Python yang didukung beserta paket yang kompatibel. Model dibuat dengan versi sklearn tercatat di results/summary.json; jika environment berbeda, training ulang di environment tujuan dan perbarui hasil/materi, bukan memaksa membuka model tak kompatibel.
5. Jalankan form, CSV, inputinvalid dan halaman evaluasi di aplikasi online. Perubahan lokal tidak otomatis mengubah server; perlu commit/redeploy.
6. Isi deployment_url di group_config.json dan jalankan build_materials.py. Link adalah opsional sesuai ketentuan; aplikasi lokal tetap dapat digunakan untuk demo.

Saat online, input dikirim ke server. Jangan menyatakan semua proses terjadi di browser. Internet lokal hanya diperlukan untuk instalasi/font; font memiliki fallback.
