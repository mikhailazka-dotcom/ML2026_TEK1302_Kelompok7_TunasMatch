"""Kontrak data dan inferensi bersama: aplikasi tidak melatih ulang model."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
APP_NAME = "TunasMatch"
TITLE = "Klasifikasi Rekomendasi Jenis Tanaman Berdasarkan Kandungan Hara Tanah dan Kondisi Iklim Menggunakan K-Nearest Neighbors, Decision Tree, dan Logistic Regression"
FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
SOURCE_URL = "https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset"
SEED = 2026
DISPLAY = {
    "N": ("Nitrogen (N)", "skala dataset"),
    "P": ("Fosfor (P)", "skala dataset"),
    "K": ("Kalium (K)", "skala dataset"),
    "temperature": ("Suhu", "°C"),
    "humidity": ("Kelembapan udara", "%"),
    "ph": ("pH tanah", "tanpa satuan"),
    "rainfall": ("Curah hujan", "mm; periode perlu dikonfirmasi"),
}
CROP_NAMES = {
    "rice": "Padi", "maize": "Jagung", "chickpea": "Chickpea (kacang arab)",
    "kidneybeans": "Kidney bean (kacang merah)", "pigeonpeas": "Kacang gude",
    "mothbeans": "Moth bean", "mungbean": "Kacang hijau", "blackgram": "Black gram",
    "lentil": "Lentil", "pomegranate": "Delima", "banana": "Pisang", "mango": "Mangga",
    "grapes": "Anggur", "watermelon": "Semangka", "muskmelon": "Melon",
    "apple": "Apel", "orange": "Jeruk", "papaya": "Pepaya", "coconut": "Kelapa",
    "cotton": "Kapas", "jute": "Jute (serat)", "coffee": "Kopi",
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def load_dataset():
    df = pd.read_csv(ROOT / "Crop_recommendation.csv")
    if list(df.columns) != FEATURES + ["label"]:
        raise ValueError("Struktur dataset berubah. Periksa urutan tujuh fitur dan label.")
    if df.isna().any().any() or df.duplicated().any():
        raise ValueError("Sumber berubah: missing/duplikat harus ditinjau sebelum training.")
    validate_inputs(df[FEATURES])
    return df


def validate_inputs(frame):
    """Tidak mengimputasi diam-diam: semua tujuh pengukuran wajib lengkap."""
    if frame.columns.duplicated().any():
        raise ValueError("Nama kolom CSV tidak boleh berulang.")
    missing = [f for f in FEATURES if f not in frame.columns]
    if missing:
        raise ValueError("Kolom wajib belum ada: " + ", ".join(missing))
    if not 1 <= len(frame) <= 10000:
        raise ValueError("CSV harus berisi 1 sampai 10.000 baris.")
    try:
        x = frame[FEATURES].apply(pd.to_numeric, errors="raise").astype(float)
    except (ValueError, TypeError) as exc:
        raise ValueError("Semua input harus angka; gunakan titik untuk desimal.") from exc
    if not np.isfinite(x.to_numpy()).all():
        raise ValueError("Input kosong, NaN, atau tak hingga tidak diperbolehkan.")
    for f in ["N", "P", "K", "rainfall"]:
        if (x[f] < 0).any():
            raise ValueError(f"{f} tidak boleh negatif.")
    if not x.humidity.between(0, 100).all():
        raise ValueError("Kelembapan harus antara 0 dan 100%.")
    if not x.ph.between(0, 14).all():
        raise ValueError("pH harus antara 0 dan 14.")
    if (x.temperature < -273.15).any():
        raise ValueError("Suhu di bawah nol absolut tidak valid.")
    return x


def range_warnings(x, bounds):
    return [f for f in FEATURES if ((x[f] < bounds[f]["min"]) | (x[f] > bounds[f]["max"])).any()]


def load_bundle():
    summary = read_json(ROOT / "results/summary.json")
    path = ROOT / "models/crop_bundle.joblib"
    if sha256(path) != summary["model_sha256"]:
        raise ValueError("Model tidak cocok dengan hasil evaluasi. Jalankan training ulang atau pulihkan artefak yang sesuai.")
    # Hanya berkas lokal tepercaya. Jangan memuat unggahan joblib pengguna.
    bundle = joblib.load(path)
    if bundle["features"] != FEATURES:
        raise ValueError("Urutan fitur model tidak cocok.")
    return bundle


def predict_frame(frame, bundle):
    x = validate_inputs(frame)
    pipeline, encoder = bundle["pipeline"], bundle["encoder"]
    probs = pipeline.predict_proba(x)
    labels = encoder.inverse_transform(pipeline.classes_.astype(int))
    ranking = np.argsort(-probs, axis=1, kind="stable")
    # predict() menjadi otoritas label; pada skor seri aturan estimator dapat berbeda.
    predictions = encoder.inverse_transform(pipeline.predict(x).astype(int))
    out = x.copy()
    out["rekomendasi"] = predictions
    out["nama_tanaman"] = [CROP_NAMES[v] for v in predictions]
    for k in range(3):
        out[f"top_{k+1}"] = labels[ranking[:, k]]
        out[f"skor_{k+1}"] = probs[np.arange(len(x)), ranking[:, k]]
    return out, pd.DataFrame(probs, columns=labels, index=x.index)
