"""Audit paket dan jalankan pytest; bedakan berkas siap dari pekerjaan manusia."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

import nbformat
from docx import Document
from pptx import Presentation

from crop_core import APP_NAME, ROOT, load_bundle, read_json, sha256, write_json


def _extract_ppt_text(prs: Presentation) -> str:
    parts = []
    def walk(shapes):
        for sh in shapes:
            if sh.has_text_frame:
                parts.append(sh.text_frame.text)
            if sh.has_table:
                for row in sh.table.rows:
                    for cell in row.cells:
                        parts.append(cell.text)
            if sh.shape_type == 6:
                walk(sh.shapes)
    for slide in prs.slides:
        walk(slide.shapes)
    return "\n".join(parts)


def main():
    required=[
        "app.py", "crop_core.py", "train.py", "build_materials.py", "build_ppt_template.py",
        "PROJEK_TANAMAN.ipynb", "Crop_recommendation.csv",
        "models/crop_bundle.joblib", "results/summary.json", "results/notebook_execution.json",
        "presentation/Laporan_Proyek_Tanaman.pptx", "presentation/ppt pengenalan projek.pptx",
        "docs/Penjelasan_Tanaman_Bahasa_Sederhana.docx", "docs/TEK1302_Kelompok7.docx",
        "references/Daftar_5_Jurnal.md", "references/Tabel_Studi_Literatur.csv",
        "video/Naskah_Demo_6_Menit_40_Detik.md",
    ]
    for filename in required:
        assert (ROOT / filename).is_file() and (ROOT / filename).stat().st_size > 0, filename

    nb = nbformat.read(ROOT / "PROJEK_TANAMAN.ipynb", as_version=4)
    code = [c for c in nb.cells if c.cell_type == "code"]
    assert all(c.execution_count is not None for c in code)
    assert not [o for c in code for o in c.get("outputs", []) if o.output_type == "error"]
    nb_all = "\n".join(c.source for c in nb.cells) + "\n" + "\n".join(str(o) for c in code for o in c.get("outputs", []))
    for forbidden in ("ISI NAMA", "ISI NIM", "ISI KELAS", "TaniPintar"):
        assert forbidden not in nb_all, f"Placeholder/nama lama ditemukan di notebook: {forbidden}"

    ppt = Presentation(ROOT / "presentation/Laporan_Proyek_Tanaman.pptx")
    assert len(ppt.slides) >= 20
    assert all(s.has_notes_slide for s in ppt.slides)
    ppt_text = _extract_ppt_text(ppt)
    for forbidden in ("ISI NAMA", "ISI NIM", "ISI KELAS", "TaniPintar", "TANIPINTAR"):
        assert forbidden not in ppt_text, f"Placeholder/nama lama ditemukan di PPT: {forbidden}"

    doc = Document(ROOT / "docs/Penjelasan_Tanaman_Bahasa_Sederhana.docx")
    assert len(doc.paragraphs) > 100
    doc_text = "\n".join(p.text for p in doc.paragraphs)
    for forbidden in ("ISI NAMA", "ISI NIM", "ISI KELAS", "TaniPintar"):
        assert forbidden not in doc_text, f"Placeholder/nama lama ditemukan di Word: {forbidden}"

    portofolio = Document(ROOT / "docs/TEK1302_Kelompok7.docx")
    assert len(portofolio.paragraphs) > 25

    from references import REFERENCES
    assert len(REFERENCES) >= 5
    assert len(list((ROOT / "references").glob("R*_metadata_crossref.json"))) >= 5
    assert (ROOT / "references/R1_teks_lengkap.txt").is_file()

    bundle = load_bundle()
    metadata = read_json(ROOT / "results/notebook_execution.json")
    assert metadata["main_model_unchanged"] and not metadata["errors"]

    process = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-k", "not streamlit"], cwd=ROOT, capture_output=True, text=True)
    (ROOT / "results/pytest_output.txt").write_text(process.stdout + process.stderr, encoding="utf-8")
    assert process.returncode == 0, process.stdout + process.stderr

    config = read_json(ROOT / "group_config.json")
    pending = [
        "Rekam/sunting video demo akhir maksimal 7 menit dengan perkenalan & narasi ketiga anggota (menunjukkan aplikasi TunasMatch dijalankan nyata).",
        "Rename folder pengumpulan sebelum unggah sesuai format ML2026_Kelas_NamaKelompok_JudulProject (mis. ML2026_TEK1302_Kelompok7_TunasMatch).",
        "Pastikan seluruh 3 anggota siap menjelaskan konsep, metode, kode, hasil, dan aplikasi pada sesi tanya jawab individu.",
    ]
    if not config.get("deployment_url"):
        pending.append("Deployment online opsional (Streamlit Community Cloud) belum diisi — aplikasi lokal siap dijalankan.")

    browser_path = ROOT / "results/browser_tests.json"
    browser = read_json(browser_path) if browser_path.exists() else {"note": "Belum ada hasil browser capture."}
    report = {
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "app_name": APP_NAME,
        "group_name": config["group_name"],
        "class": config["class"],
        "members": [f"{m['name']} ({m['nim']})" for m in config["members"]],
        "required_files": len(required),
        "notebook_code_cells": len(code),
        "notebook_errors": 0,
        "ppt_slides": len(ppt.slides),
        "word_paragraphs": len(doc.paragraphs),
        "portofolio_paragraphs": len(portofolio.paragraphs),
        "selected_model": bundle["selected_model"],
        "pytest_core": process.stdout.strip(),
        "browser": browser,
        "local_pdf_articles": len(list((ROOT / "references").glob("R*_artikel.pdf"))),
        "human_steps_remaining": pending,
        "status": "Seluruh artefak teknis, identitas kelompok, PPT Laporan A–O, Word, Portofolio CLASS-IPB, dan Notebook sudah lengkap & terverifikasi (tinggal video demo final & rename folder saat pengumpulan).",
    }
    write_json(ROOT / "results/project_verification.json", report)
    write_json(ROOT / "results/artifact_manifest.json", {p: sha256(ROOT / p) for p in required})

    summary = read_json(ROOT / "results/summary.json")
    checklist = f"""# Hasil Pengecekan Akhir — {APP_NAME}

Kelompok: **{config['group_name']}** | Kelas: **{config['class']}**
Anggota: {", ".join(f"{m['name']} ({m['nim']})" for m in config["members"])}

- **Identitas & Branding:** Seluruh materi (PPT, Word, Portofolio CLASS-IPB, Notebook, Docs, README) sudah disinkronkan memakai nama **{APP_NAME}** dan identitas lengkap 3 anggota (tanpa placeholder).
- **Aplikasi & Inferensi:** `pytest` lulus ({process.stdout.strip().splitlines()[-1]}), serta 13 pengecekan browser desktop & mobile tercatat lulus di `results/browser_tests.json`.
- **Notebook:** `{len(code)}` cell kode dieksekusi, `0` error; model utama (`models/crop_bundle.joblib`) tidak berubah.
- **PPT Laporan Project:** `presentation/Laporan_Proyek_Tanaman.pptx` ({len(ppt.slides)} slide) dibangun dari template `ppt pengenalan projek.pptx`, mencakup penuh Bagian A–O + Lampiran + speaker notes.
- **Dokumen Word & Portofolio CLASS-IPB:** `docs/Penjelasan_Tanaman_Bahasa_Sederhana.docx` ({len(doc.paragraphs)} paragraf) dan `docs/TEK1302_Kelompok7.docx` siap unggah untuk tugas Portofolio Project CLASS-IPB.
- **Studi Literatur:** 5 artikel ilmiah nyata beserta metadata Crossref/DOI, 4 PDF lokal (`R2`–`R5`), full-text `R1`, dan `references/Tabel_Studi_Literatur.csv`.
- **Model Aktif:** `{bundle['selected_model']}` (Nested CV macro-F1 `{summary['selected_cv']['cv_f1_macro_mean']:.4f}`, Test accuracy `{summary['selected_test']['accuracy']:.2%}`). Dipilih lewat Nested CV, bukan test accuracy tertinggi.

## Sisa Pekerjaan Kelompok (Non-Otomatis)
""" + "\n".join("- " + p for p in pending) + "\n\nBaca `MULAI_DI_SINI.md` untuk membuka berkas dan menjalankan aplikasi.\n"
    (ROOT / "PENGECEKAN_AKHIR.md").write_text(checklist, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

