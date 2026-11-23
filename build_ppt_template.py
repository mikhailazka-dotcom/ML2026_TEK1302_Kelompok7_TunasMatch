"""Bangun PPT Laporan Project (Bagian A–O) menggunakan template ppt pengenalan projek.pptx."""
from __future__ import annotations

import copy
from pathlib import Path

import pandas as pd
from PIL import Image as PILImage
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from crop_core import APP_NAME, ROOT, SOURCE_URL, TITLE, read_json
from references import REFERENCES

TEMPLATE_PATH = ROOT / "presentation/ppt pengenalan projek.pptx"
OUTPUT_PATH = ROOT / "presentation/Laporan_Proyek_Tanaman.pptx"

DARK_GREEN = RGBColor(0x22, 0x39, 0x15)
MID_GREEN = RGBColor(0x3A, 0x60, 0x24)
ACCENT_GREEN = RGBColor(0x68, 0xA8, 0x42)
SOFT_ROW = RGBColor(0xED, 0xF5, 0xE6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK_TEXT = RGBColor(0x18, 0x2B, 0x0F)
MUTED_LIGHT = RGBColor(0xDF, 0xEC, 0xD5)


def _clone_slide(prs: Presentation, src_idx: int):
    src = prs.slides[src_idx]
    dst = prs.slides.add_slide(prs.slide_layouts[6])
    rid_map = {}
    for rel in src.part.rels.values():
        if "slideLayout" in rel.reltype:
            continue
        if rel.is_external:
            new_rid = dst.part.relate_to(rel.target_ref, rel.reltype, is_external=True)
        else:
            new_rid = dst.part.relate_to(rel.target_part, rel.reltype)
        rid_map[rel.rId] = new_rid

    for el in src.shapes._spTree:
        tag = el.tag.split("}")[-1]
        if tag in ("nvGrpSpPr", "grpSpPr"):
            continue
        cloned = copy.deepcopy(el)
        for node in cloned.iter():
            for attr in list(node.attrib):
                if attr.endswith("}embed") or attr.endswith("}link") or attr.endswith("}id"):
                    val = node.attrib[attr]
                    if val in rid_map:
                        node.attrib[attr] = rid_map[val]
        dst.shapes._spTree.append(cloned)
    return dst


def _find_shape(container, name: str):
    for sh in container.shapes:
        if sh.name == name:
            return sh
        if sh.shape_type == 6:
            found = _find_shape(sh, name)
            if found is not None:
                return found
    return None


def _remove_by_names(slide, names: set[str]):
    spTree = slide.shapes._spTree
    for sh in list(slide.shapes):
        if sh.name in names:
            spTree.remove(sh._element)


def _set_box(shape, left=None, top=None, width=None, height=None):
    if left is not None:
        shape.left = Inches(left)
    if top is not None:
        shape.top = Inches(top)
    if width is not None:
        shape.width = Inches(width)
    if height is not None:
        shape.height = Inches(height)


def _set_text(
    shape,
    text: str,
    size: float | None = None,
    bold: bool | None = None,
    color: RGBColor | None = None,
    align=PP_ALIGN.LEFT,
    line_spacing: float = 1.15,
    space_after: float = 5,
):
    tf = shape.text_frame
    tf.word_wrap = True
    first_p = tf.paragraphs[0]
    ref_font_name = "Garet"
    ref_size = Pt(24)
    ref_bold = None
    ref_color = None
    if first_p.runs:
        r0 = first_p.runs[0]
        if r0.font.name:
            ref_font_name = r0.font.name
        if r0.font.size:
            ref_size = r0.font.size
        ref_bold = r0.font.bold
        try:
            if r0.font.color and r0.font.color.type is not None:
                ref_color = r0.font.color.rgb
        except Exception:
            ref_color = None

    # Bersihkan seluruh paragraf & reset properti pPr bawaan Canva agar spasi seragam
    for p in list(tf.paragraphs)[1:]:
        p._p.getparent().remove(p._p)
    first_p.clear()
    pPr = first_p._p.find(qn("a:pPr"))
    if pPr is not None:
        first_p._p.remove(pPr)

    lines = str(text).split("\n")
    for idx, line in enumerate(lines):
        p = first_p if idx == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        p.space_before = Pt(0)
        p.space_after = Pt(space_after)
        run = p.add_run()
        run.text = line
        run.font.name = ref_font_name
        run.font.size = Pt(size) if size is not None else ref_size
        if bold is not None:
            run.font.bold = bold
        elif ref_bold is not None:
            run.font.bold = ref_bold
        if color is not None:
            run.font.color.rgb = color
        elif ref_color is not None:
            run.font.color.rgb = ref_color


def _add_textbox(
    slide,
    text: str,
    x: float,
    y: float,
    w: float,
    h: float,
    font_name: str = "Garet",
    size: float = 20,
    bold: bool = False,
    color: RGBColor = WHITE,
    align=PP_ALIGN.LEFT,
    space_after: float = 5,
    line_spacing: float = 1.15,
):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.04)
    tf.margin_right = Inches(0.04)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    for idx, line in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)
        run = p.add_run()
        run.text = line
        run.font.name = font_name
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
    return tb


def _add_badge_and_footer(slide, section_label: str, page_num: int, total_pages: int, light_footer: bool = True):
    pill_w = max(5.8, min(8.2, len(section_label) * 0.165 + 0.9))
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.12), Inches(0.45), Inches(pill_w), Inches(0.52))
    pill.adjustments[0] = 0.25
    pill.fill.solid()
    pill.fill.fore_color.rgb = MID_GREEN
    pill.line.fill.background()
    tf = pill.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = section_label.upper()
    r.font.name = "Garet Bold"
    r.font.size = Pt(14.5)
    r.font.bold = True
    r.font.color.rgb = WHITE

    fcol = MUTED_LIGHT if light_footer else MID_GREEN
    _add_textbox(
        slide,
        f"{APP_NAME}  |  Kelompok 7  |  {page_num:02d} / {total_pages:02d}",
        13.8,
        10.56,
        5.5,
        0.44,
        font_name="Garet Bold" if not light_footer else "Garet",
        size=14,
        bold=not light_footer,
        color=fcol,
        align=PP_ALIGN.RIGHT,
        space_after=0,
    )


def _add_image_card(slide, img_path: Path, x: float, y: float, w: float, h: float, pad: float = 0.2):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    card.adjustments[0] = 0.04
    card.fill.solid()
    card.fill.fore_color.rgb = WHITE
    card.line.color.rgb = ACCENT_GREEN
    card.line.width = Pt(1.75)

    with PILImage.open(img_path) as im:
        ratio = im.width / im.height
    max_w = w - 2 * pad
    max_h = h - 2 * pad
    if max_w / max_h > ratio:
        ph = max_h
        pw = ph * ratio
    else:
        pw = max_w
        ph = pw / ratio
    px = x + (w - pw) / 2
    py = y + (h - ph) / 2
    slide.shapes.add_picture(str(img_path), Inches(px), Inches(py), width=Inches(pw), height=Inches(ph))


def _add_table(slide, headers, rows, x: float, y: float, w: float, h: float, col_widths: list[float], font_size: float = 15.5):
    shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = shape.table
    for col, cw in zip(tbl.columns, col_widths):
        col.width = Inches(cw)
    for r_idx, row in enumerate([headers] + rows):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.12)
            cell.margin_right = Inches(0.12)
            cell.margin_top = Inches(0.08)
            cell.margin_bottom = Inches(0.08)
            cell.fill.solid()
            if r_idx == 0:
                cell.fill.fore_color.rgb = ACCENT_GREEN
            else:
                cell.fill.fore_color.rgb = WHITE if r_idx % 2 == 1 else SOFT_ROW
            tf = cell.text_frame
            tf.word_wrap = True
            for p_idx, line in enumerate(str(val).split("\n")):
                p = tf.paragraphs[0] if p_idx == 0 else tf.add_paragraph()
                p.alignment = PP_ALIGN.LEFT
                p.line_spacing = 1.12
                run = p.add_run()
                run.text = line
                run.font.name = "Garet Bold" if r_idx == 0 else "Garet"
                run.font.size = Pt(font_size if r_idx > 0 else font_size + 0.5)
                run.font.bold = r_idx == 0
                run.font.color.rgb = WHITE if r_idx == 0 else DARK_TEXT
    return tbl


def _set_notes(slide, text: str):
    slide.notes_slide.notes_text_frame.text = text.strip()


def _delete_first_n_slides(prs: Presentation, n: int):
    sldIdLst = prs.slides._sldIdLst
    for _ in range(n):
        sldId = sldIdLst[0]
        rId = sldId.get(qn("r:id"))
        prs.part.drop_rel(rId)
        sldIdLst.remove(sldId)


def _format_slide6_left(sl, title: str, subtitle: str, body: str, title_size=56, sub_size=21, body_size=18.5):
    t = _find_shape(sl, "TextBox 20")
    _set_box(t, left=1.12, top=1.22, width=8.9, height=2.5)
    _set_text(t, title, size=title_size, bold=True, color=DARK_GREEN, line_spacing=1.05, space_after=0)
    s = _find_shape(sl, "TextBox 18")
    _set_box(s, left=0.72, top=4.38, width=9.1, height=0.95)
    _set_text(s, subtitle, size=sub_size, bold=True, color=WHITE, line_spacing=1.12, space_after=2)
    b = _find_shape(sl, "TextBox 19")
    _set_box(b, left=0.72, top=5.42, width=9.15, height=4.65)
    _set_text(b, body, size=body_size, bold=False, color=WHITE, line_spacing=1.16, space_after=7)


def _format_slide3_header(sl, title: str, subtitle: str, title_size=60, sub_size=21):
    t = _find_shape(sl, "TextBox 27")
    _set_box(t, left=1.12, top=1.12, width=13.5, height=2.2)
    _set_text(t, title, size=title_size, bold=True, color=DARK_GREEN, line_spacing=1.05, space_after=0)
    s = _find_shape(sl, "TextBox 14")
    _set_box(s, left=1.12, top=4.05, width=15.8, height=0.72)
    _set_text(s, subtitle, size=sub_size, bold=True, color=WHITE, line_spacing=1.12, space_after=0)


def _format_slide5_header(sl, title: str, subtitle: str, title_size=58, sub_size=22):
    t = _find_shape(sl, "TextBox 39")
    _set_box(t, left=1.12, top=1.15, width=13.5, height=2.6)
    _set_text(t, title, size=title_size, bold=True, color=DARK_GREEN, line_spacing=1.05, space_after=0)
    s = _find_shape(sl, "TextBox 35")
    _set_box(s, left=1.12, top=4.62, width=16.2, height=0.85)
    _set_text(s, subtitle, size=sub_size, bold=True, color=WHITE, line_spacing=1.15, space_after=0)


def build_ppt_from_template(s: dict, config: dict, cv: pd.DataFrame, test: pd.DataFrame) -> Path:
    """Bangun 22 slide Laporan Project (Bagian A–O + Lampiran + Penutup) memakai template ppt pengenalan projek.pptx."""
    prs = Presentation(TEMPLATE_PATH)
    n_orig = len(prs.slides)
    total_pages = 22
    best = s["selected_model"]
    tuning = read_json(ROOT / "results/tuning.json")
    members = config["members"]
    kelas = config["class"]
    group_name = config["group_name"]
    imp = pd.read_csv(ROOT / "results/feature_importance_dt.csv")
    sc = pd.read_csv(ROOT / "results/scaling_experiment.csv")
    cv_map = cv.set_index("model")
    test_map = test.set_index("model")

    # ── SLIDE 01: A. Judul Project (Template Slide 1 - Cover) ─────────────────
    sl = _clone_slide(prs, 0)
    top_lbl = _find_shape(sl, "TextBox 25")
    _set_text(top_lbl, f"{kelas.upper()}", size=19, bold=True, color=WHITE, line_spacing=1.08, space_after=0)
    title_box = _find_shape(sl, "TextBox 22")
    _set_box(title_box, left=0.74, top=2.18, width=12.15, height=3.95)
    _set_text(
        title_box,
        f"{APP_NAME.upper()}:\nKLASIFIKASI REKOMENDASI JENIS TANAMAN\nBERDASARKAN HARA TANAH & IKLIM",
        size=44,
        bold=True,
        color=DARK_GREEN,
        line_spacing=1.12,
        space_after=4,
    )
    _add_textbox(
        sl,
        "K-Nearest Neighbors  ·  Decision Tree  ·  Logistic Regression   |   Laporan Akhir Project ML",
        0.74,
        6.48,
        12.1,
        0.52,
        font_name="Garet Bold",
        size=18.5,
        bold=True,
        color=MID_GREEN,
        space_after=0,
    )
    tb30 = _find_shape(sl, "TextBox 30")
    tb31 = _find_shape(sl, "TextBox 31")
    tb32 = _find_shape(sl, "TextBox 32")
    _set_text(tb30, "Presented By", size=22, bold=False, color=WHITE, space_after=0)
    _set_box(tb31, width=9.2, height=0.58)
    _set_text(tb31, f"{group_name}  •  {kelas}", size=21, bold=True, color=WHITE, space_after=0)
    member_lines = "\n".join(f"{m['name']}  ({m['nim']})" for m in members)
    _set_text(tb32, member_lines, size=20.5, bold=False, color=WHITE, line_spacing=1.18, space_after=2)
    _set_notes(
        sl,
        f"Slide 1 (Bagian A - Judul Project): {TITLE}. Aplikasi {APP_NAME}, {group_name}, kelas {kelas}. "
        f"Anggota: {', '.join(m['name'] + ' (' + m['nim'] + ')' for m in members)}.",
    )

    # ── SLIDE 02: B. Latar Belakang & Masalah (Template Slide 2) ──────────────
    sl = _clone_slide(prs, 1)
    _add_badge_and_footer(sl, "Bagian B • Latar Belakang & Masalah", 2, total_pages, light_footer=False)
    t = _find_shape(sl, "TextBox 19")
    _set_box(t, left=1.12, top=1.2, width=13.5, height=2.2)
    _set_text(t, "LATAR BELAKANG & MASALAH", size=64, bold=True, color=DARK_GREEN, line_spacing=1.05, space_after=0)
    sub = _find_shape(sl, "TextBox 14")
    _set_box(sub, left=1.12, top=4.35, width=14.0, height=0.95)
    _set_text(
        sub,
        "Pemilihan tanaman tanpa data hara tanah dan iklim berisiko menurunkan kecocokan budidaya",
        size=27,
        bold=True,
        color=WHITE,
        line_spacing=1.12,
        space_after=0,
    )
    body = _find_shape(sl, "TextBox 15")
    _set_box(body, left=1.12, top=5.62, width=14.6, height=3.85)
    _set_text(
        body,
        "• Kondisi nyata: Setiap komoditas membutuhkan kadar unsur hara (N, P, K), pH, suhu, kelembapan udara, dan curah hujan yang berbeda.\n"
        "• Permasalahan: Penentuan jenis tanaman secara perkiraan semata rentan salah pilih dan menurunkan efisiensi lahan.\n"
        "• Alasan & urgensi: Pendekatan Machine Learning mampu mempelajari pola multivariat secara objektif, cepat, dan terukur dari data.\n"
        "• Ruang lingkup jujur: TunasMatch memprediksi label tanaman dari dataset historis sebagai alat bantu belajar pola, bukan jaminan hasil panen.",
        size=20.5,
        bold=False,
        color=WHITE,
        line_spacing=1.2,
        space_after=8,
    )
    _set_notes(sl, "Bagian B: Jelaskan kondisi, permasalahan, alasan memilih masalah pertanian presisi, urgensi solusi berbasis ML, serta batasan klaim secara jujur.")

    # ── SLIDE 03: C. Tujuan Project (Template Slide 4) ────────────────────────
    sl = _clone_slide(prs, 3)
    _add_badge_and_footer(sl, "Bagian C • Tujuan Project", 3, total_pages, light_footer=False)
    t = _find_shape(sl, "TextBox 21")
    _set_box(t, left=1.12, top=1.25, width=12.0, height=1.8)
    _set_text(t, "TUJUAN PROJECT", size=68, bold=True, color=DARK_GREEN, line_spacing=1.05, space_after=0)
    sub = _find_shape(sl, "TextBox 19")
    _set_box(sub, left=1.12, top=4.35, width=14.0, height=0.85)
    _set_text(sub, "Target terukur dari eksperimen hingga aplikasi TunasMatch", size=28, bold=True, color=WHITE, space_after=0)
    body = _find_shape(sl, "TextBox 20")
    _set_box(body, left=6.44, top=5.55, width=9.95, height=3.95)
    _set_text(
        body,
        "1. Membangun model klasifikasi multikelas untuk merekomendasikan 1 dari 22 jenis tanaman dari 7 parameter tanah & iklim.\n"
        "2. Membandingkan 3 algoritma (KNN, Decision Tree, Logistic Regression) secara adil dengan Nested CV bebas data leakage.\n"
        "3. Menganalisis kesalahan prediksi per kelas, overfitting, feature importance, dan pengaruh scaling.\n"
        "4. Mengimplementasikan model terpilih ke aplikasi web interaktif TunasMatch (input tunggal & batch CSV).",
        size=20,
        bold=False,
        color=WHITE,
        line_spacing=1.18,
        space_after=8,
    )
    _set_notes(sl, "Bagian C: Empat target konkret yang dicapai mulai dari pemodelan klasifikasi multikelas sampai implementasi aplikasi Streamlit TunasMatch.")

    # ── SLIDE 04: D. Studi Literatur 1/2 (Template Slide 3 canvas + Table) ────
    sl = _clone_slide(prs, 2)
    _remove_by_names(sl, {f"TextBox {k}" for k in range(15, 27)})
    _add_badge_and_footer(sl, "Bagian D • Studi Literatur (1/2)", 4, total_pages, light_footer=True)
    _format_slide3_header(
        sl,
        "STUDI LITERATUR (R1 – R3)",
        "Ringkasan jurnal referensi utama (2022–2025) sebagai landasan masalah, metode, dan evaluasi",
    )
    lit_rows_1 = [
        [
            "R1\nThilakarathne et al. (2022)\nSensors",
            "Rekomendasi tanaman + cloud precision farming.\nKaggle 2.200 baris, 7 fitur + label.",
            "KNN, DT, RF, XGB, SVM.\nMetrik: Acc, P, R, F1, 10-fold CV.",
            "RF terbaik: Acc 97,18%, F1 97%, CV 97,40%.\nBeda: Kami fokus 3 model transparan, nested CV, error per kelas, & Streamlit lokal.",
        ],
        [
            "R2\nShastri et al. (2025)\nScientific Reports",
            "Perbandingan model & explainability rekomendasi.\nKaggle 2.200 baris, 22 kelas (split 75:25).",
            "10 model supervised (incl. GB) + LIME.\nMetrik: Acc, P, R, F1, ROC.",
            "GB tertinggi: Acc 99,27%, F1 99,32%.\nBeda: Tanpa GB/LIME; fokus seleksi nested CV, analisis pasangan tertukar & ablation scaling.",
        ],
        [
            "R3\nSingh & Sharma (2025)\nScientific Reports",
            "Rekomendasi berbasis cloud + notifikasi SMS.\n3.000 baris, 8 kolom (berbeda dari CSV kami).",
            "TCRM vs LR, KNN, AdaBoost.\nMetrik: Acc, P, R, F1, 5-fold CV.",
            "TCRM Acc 94%, F1 93,97%, CV 97,67%.\nBeda: Tanpa klaim IoT/SMS cloud; prototipe lokal terverifikasi SHA-256 pada 2.200 baris.",
        ],
    ]
    _add_table(
        sl,
        ["Ref. & Penulis", "Permasalahan & Dataset", "Algoritma & Metrik", "Hasil Utama & Perbedaan dengan Project"],
        lit_rows_1,
        x=1.12,
        y=4.92,
        w=17.8,
        h=5.25,
        col_widths=[3.2, 4.4, 3.8, 6.4],
        font_size=15,
    )
    _set_notes(sl, "Bagian D (1/2): R1-R3. Angka jurnal berasal dari laporan asli penulis (bukan replikasi). Tabel 9 kolom lengkap tersedia di references/Tabel_Studi_Literatur.md dan .csv.")

    # ── SLIDE 05: D. Studi Literatur 2/2 (Template Slide 3 canvas + Table) ────
    sl = _clone_slide(prs, 2)
    _remove_by_names(sl, {f"TextBox {k}" for k in range(15, 27)})
    _add_badge_and_footer(sl, "Bagian D • Studi Literatur (2/2)", 5, total_pages, light_footer=True)
    _format_slide3_header(
        sl,
        "STUDI LITERATUR (R4 – R5)",
        "Landasan keputusan preprocessing, interpretabilitas, dan posisi project TunasMatch",
    )
    lit_rows_2 = [
        [
            "R4\nVenkateswara & Padmanaban (2025)\nScientific Reports",
            "Rekomendasi tanaman & pupuk tabular.\nDataset Western Maharashtra (tugas berbeda).",
            "TabNet, SHAP, iterative imputation, SMOTE; 5-fold CV.\nMetrik: Accuracy & CV.",
            "Acc tanaman 96,21%, pupuk 95,24%.\nBeda: Data kami seimbang & lengkap → tidak menyalin SMOTE/imputasi yang tidak diperlukan.",
        ],
        [
            "R5\nDhingra et al. (2026)\nScientific Reports (Accepted)",
            "Rekomendasi transparan + skenario what-if.\n7 fitur N/P/K/pH/suhu/kelembapan/hujan, 22 kelas.",
            "LightGBM, SHAP, counterfactual; dashboard Streamlit.\nMetrik: Test Acc, Macro-F1.",
            "Test Acc 99,39%, Macro-F1 0,9900; menegaskan benchmark ≠ siap lapangan.\nBeda: Fokus 3 model klasik, nested CV, error per kelas & dokumentasi pemula.",
        ],
    ]
    _add_table(
        sl,
        ["Ref. & Penulis", "Permasalahan & Dataset", "Algoritma & Metrik", "Hasil Utama & Perbedaan dengan Project"],
        lit_rows_2,
        x=1.12,
        y=4.92,
        w=17.8,
        h=3.65,
        col_widths=[3.4, 4.3, 3.8, 6.3],
        font_size=15,
    )
    box = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.12), Inches(8.85), Inches(17.8), Inches(1.4))
    box.adjustments[0] = 0.08
    box.fill.solid()
    box.fill.fore_color.rgb = DARK_GREEN
    box.line.color.rgb = ACCENT_GREEN
    box.line.width = Pt(1.5)
    _add_textbox(
        sl,
        "Sintesis 5 Jurnal → Keputusan Project TunasMatch: (1) Memilih 7 fitur baku tanah & iklim, (2) Tidak asal menerapkan SMOTE/imputasi karena data seimbang & lengkap, (3) Menggunakan Macro-F1 + Nested CV anti-leakage, (4) Mengimplementasikan dashboard Streamlit lokal dengan peringatan batasan jujur.",
        1.34,
        9.02,
        17.35,
        1.1,
        font_name="Garet",
        size=16,
        color=WHITE,
        space_after=0,
    )
    _set_notes(sl, "Bagian D (2/2): R4 dan R5 beserta sintesis bagaimana 5 jurnal mengarahkan desain preprocessing, algoritma, metrik evaluasi, dan implementasi Streamlit TunasMatch.")

    # ── SLIDE 06: E. Dataset (Template Slide 3 + Table) ───────────────────────
    sl = _clone_slide(prs, 2)
    _remove_by_names(sl, {f"TextBox {k}" for k in range(15, 27)})
    _add_badge_and_footer(sl, "Bagian E • Dataset", 6, total_pages, light_footer=True)
    _format_slide3_header(
        sl,
        "DATASET & KARAKTERISTIK",
        "Crop Recommendation Dataset (Kaggle — Atharva Ingle): 2.200 baris × 8 kolom, 22 kelas seimbang",
    )
    ds_rows = [
        ["N, P, K", "int64 (numerik)", "Kandungan unsur hara Nitrogen, Fosfor, Kalium (skala dataset; bukan dosis pupuk)"],
        ["temperature", "float64 (°C)", "Suhu udara lingkungan pada kondisi contoh (rentang 8,83 – 43,68 °C)"],
        ["humidity", "float64 (%)", "Kelembapan relatif udara, bukan kadar air tanah (rentang 14,26 – 99,98 %)"],
        ["ph", "float64 (tanpa satuan)", "Tingkat keasaman/kebasaan tanah (rentang 3,50 – 9,94)"],
        ["rainfall", "float64 (mm)", "Curah hujan (rentang 20,21 – 298,56 mm; periode akumulasi belum tercantum di CSV)"],
        ["label (Target)", "object (22 kelas)", "Nama jenis tanaman (rice, maize, jute, coffee, dll.) — tepat 100 baris per kelas"],
    ]
    _add_table(
        sl,
        ["Variabel / Fitur", "Tipe & Satuan", "Arti Variabel & Catatan Karakteristik"],
        ds_rows,
        x=1.12,
        y=4.92,
        w=17.8,
        h=4.35,
        col_widths=[3.1, 3.3, 11.4],
        font_size=15,
    )
    _add_textbox(
        sl,
        "Audit kualitas data lokal (data/source_manifest.json): Missing value = 0  |  Duplikat = 0  |  Distribusi kelas = Seimbang sempurna (22 × 100)  |  Konteks literatur (R1): India & augmentasi.",
        1.12,
        9.48,
        17.8,
        0.8,
        font_name="Garet Bold",
        size=15.5,
        bold=True,
        color=MUTED_LIGHT,
    )
    _set_notes(sl, f"Bagian E: Sumber {SOURCE_URL}. Jelaskan 2.200 baris, 7 fitur numerik, 1 target 22 kelas, tipe data, 0 missing, 0 duplikat, dan catatan jujur mengenai satuan NPK & periode hujan.")

    # ── SLIDE 07: F. EDA 1/2 (Template Slide 6 - Text Left + Plot Right) ──────
    sl = _clone_slide(prs, 5)
    _remove_by_names(sl, {"Freeform 17"})
    _add_badge_and_footer(sl, "Bagian F • Exploratory Data Analysis (1/2)", 7, total_pages, light_footer=False)
    _format_slide6_left(
        sl,
        "EDA: DISTRIBUSI & OUTLIER",
        "Audit keseimbangan kelas & peninjauan outlier per kelas",
        "• Kelas seimbang: Tepat 100 contoh untuk setiap dari 22 tanaman → tidak membutuhkan SMOTE atau class weighting.\n"
        "• EDA fitur hanya dari data training (1.760 baris) agar bebas data leakage.\n"
        "• Interpretasi outlier (IQR): Nilai Kalium (K) yang tampak ekstrem pada boxplot global ternyata wajar mengelompok khusus pada kelas apel dan anggur.\n"
        "• Keputusan: Outlier tidak dihapus otomatis karena mencerminkan karakteristik biologis/kelas tanaman di dataset.",
        body_size=19,
    )
    _add_image_card(sl, ROOT / "plots/kalium_per_kelas.png", 10.25, 2.25, 9.15, 7.75)
    _set_notes(sl, "Bagian F (1/2): Grafik kalium per kelas menunjukkan mengapa metode IQR global tidak boleh langsung dipakai membuang baris: apel dan anggur memiliki rentang K tinggi yang konsisten.")

    # ── SLIDE 08: F. EDA 2/2 (Template Slide 6 - Text Left + Plot Right) ──────
    sl = _clone_slide(prs, 5)
    _remove_by_names(sl, {"Freeform 17"})
    _add_badge_and_footer(sl, "Bagian F • Exploratory Data Analysis (2/2)", 8, total_pages, light_footer=False)
    _format_slide6_left(
        sl,
        "EDA: KEMIRIPAN & KORELASI",
        "Sebagian kelompok tanaman memiliki pola kondisi tumpang tindih",
        "• Padi vs Jute: Kelembapan dan sebagian rentang curah hujan berdekatan → berpotensi menjadi sumber salah klasifikasi.\n"
        "• Kacang-kacangan (lentil, mothbeans, blackgram, pigeonpeas): Tumpang tindih pada proyeksi 2 fitur (P & humidity) sehingga model harus memanfaatkan ketujuh fitur sekaligus.\n"
        "• Korelasi training: Pasangan P dan K berkorelasi positif kuat (r ≈ 0,74); korelasi menunjukkan hubungan linear antarfitur, bukan sebab-akibat.\n"
        "• Rentang skala fitur sangat berbeda (pH ~3–9 vs rainfall ~20–298) → menjadi dasar scaling bagi KNN & LR.",
        body_size=18.5,
    )
    _add_image_card(sl, ROOT / "plots/scatter_kemiripan.png", 10.25, 2.25, 9.15, 7.75)
    _set_notes(sl, "Bagian F (2/2): Scatter plot membantu memprediksi sejak awal kelas mana yang rawan tertukar (padi-jute dan kelompok kacang-kacangan), serta menunjukkan perbedaan skala fitur.")

    # ── SLIDE 09: G. Preprocessing Data (Template Slide 7 - 3-Step Flow) ──────
    sl = _clone_slide(prs, 6)
    _add_badge_and_footer(sl, "Bagian G • Preprocessing Data", 9, total_pages, light_footer=True)
    t = _find_shape(sl, "TextBox 33")
    _set_box(t, left=1.12, top=1.18, width=13.5, height=1.3)
    _set_text(t, "PREPROCESSING DATA", size=64, bold=True, color=DARK_GREEN, space_after=0)
    sub = _find_shape(sl, "TextBox 26")
    _set_box(sub, left=1.12, top=3.05, width=15.0, height=0.8)
    _set_text(sub, "Tahapan dipilih sesuai kebutuhan dataset & algoritma — bebas data leakage", size=25, bold=True, color=WHITE, space_after=0)
    _set_text(_find_shape(sl, "TextBox 27"), "1. Validasi & Split 80:20", size=23, bold=True, color=WHITE, space_after=0)
    _set_text(
        _find_shape(sl, "TextBox 30"),
        "Cek missing=0, duplikat=0, nilai fisik valid. Split stratified 80:20 (1.760 train, 440 test, seed 2026). Tanpa SMOTE/imputasi palsu.",
        size=18,
        color=WHITE,
    )
    _set_text(_find_shape(sl, "TextBox 28"), "2. LabelEncoder Target", size=23, bold=True, color=WHITE, space_after=0)
    _set_text(
        _find_shape(sl, "TextBox 31"),
        "Mengubah 22 nama tanaman ke ID 0–21 (non-ordinal). Di-fit hanya pada y_train lalu disimpan dalam bundle untuk inferensi.",
        size=18,
        color=WHITE,
    )
    _set_text(_find_shape(sl, "TextBox 29"), "3. StandardScaler di Pipeline", size=23, bold=True, color=WHITE, space_after=0)
    _set_text(
        _find_shape(sl, "TextBox 32"),
        "z = (x − μ_train) / σ_train dipasang khusus pada KNN & Logistic Regression di dalam Pipeline. Decision Tree tanpa scaler. Fit hanya di fold latih.",
        size=18,
        color=WHITE,
    )
    note_box = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.17), Inches(7.32), Inches(9.65), Inches(2.6))
    note_box.adjustments[0] = 0.06
    note_box.fill.solid()
    note_box.fill.fore_color.rgb = DARK_GREEN
    note_box.line.color.rgb = ACCENT_GREEN
    note_box.line.width = Pt(1.5)
    _add_textbox(
        sl,
        "MENGAPA TIDAK SEMUA PREPROCESSING DIPAKAI?\n"
        "• Tidak ada imputasi karena dataset lengkap (0 missing); input kosong pada aplikasi justru ditolak.\n"
        "• Tidak ada SMOTE/oversampling karena distribusi 22 kelas sudah seimbang (100/kelas).\n"
        "• Tidak ada penghapusan outlier otomatis karena nilai ekstrem mencerminkan variasi antar-tanaman.",
        9.42,
        7.48,
        9.15,
        2.3,
        font_name="Garet",
        size=16.5,
        color=WHITE,
        space_after=4,
    )
    _set_notes(sl, "Bagian G: Tegaskan alasan setiap keputusan preprocessing dan pencegahan data leakage (scaler hanya fit pada 1.760 data training / fold training, diverifikasi oleh unit test).")

    # ── SLIDE 10: H. Pengembangan Model 1/2 (Template Slide 5 - 3 Cards) ──────
    sl = _clone_slide(prs, 4)
    _add_badge_and_footer(sl, "Bagian H • Pengembangan Model (1/2)", 10, total_pages, light_footer=True)
    _format_slide5_header(
        sl,
        "PENGEMBANGAN MODEL ML",
        "Perbandingan 3 paradigma klasifikasi berbeda (berbasis jarak, aturan pohon, dan batas linear)",
    )
    _set_text(_find_shape(sl, "TextBox 32"), "K-Nearest Neighbors", size=23, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER, space_after=0)
    _set_text(_find_shape(sl, "TextBox 33"), "Decision Tree", size=23, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER, space_after=0)
    _set_text(_find_shape(sl, "TextBox 34"), "Logistic Regression", size=23, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER, space_after=0)
    _set_text(
        _find_shape(sl, "TextBox 36"),
        "• Menebak kelas dari k tetangga terdekat di ruang 7 fitur.\n• Non-linear & fleksibel untuk klaster lokal.\n• Membutuhkan StandardScaler; sensitif terhadap k dan jarak (L1/L2).",
        size=17.5,
        color=WHITE,
        align=PP_ALIGN.LEFT,
        space_after=6,
    )
    _set_text(
        _find_shape(sl, "TextBox 37"),
        "• Membagi data lewat serangkaian aturan ambang (mis. curah hujan, kelembapan).\n• Sangat interpretabel & tanpa scaling.\n• Rentan overfitting jika kedalaman pohon tidak dibatasi.",
        size=17.5,
        color=WHITE,
        align=PP_ALIGN.LEFT,
        space_after=6,
    )
    _set_text(
        _find_shape(sl, "TextBox 38"),
        "• Menghitung skor bobot linear & probabilitas untuk 22 kelas.\n• Cepat, stabil, & baseline kuat terhadap overfitting.\n• Membutuhkan StandardScaler & pengaturan regularisasi C.",
        size=17.5,
        color=WHITE,
        align=PP_ALIGN.LEFT,
        space_after=6,
    )
    _set_notes(sl, "Bagian H (1/2): Jelaskan alasan metodologis pemilihan 3 algoritma berbeda paradigma, bukan mencoba algoritma secara acak.")

    # ── SLIDE 11: H. Pengembangan Model 2/2 (Template Slide 3 + Table) ────────
    sl = _clone_slide(prs, 2)
    _remove_by_names(sl, {f"TextBox {k}" for k in range(15, 27)})
    _add_badge_and_footer(sl, "Bagian H • Pengembangan Model (2/2)", 11, total_pages, light_footer=True)
    _format_slide3_header(
        sl,
        "TRAINING, VALIDASI & TUNING",
        "Stratified 80:20 (seed 2026) + Nested CV (Outer 5-fold, Inner 3-fold) + Final GridSearch 5-fold",
    )
    tun_rows = [
        [
            "K-Nearest Neighbors\n(Pipeline: Scaler → KNN)",
            "n_neighbors: [3, 5, 7, 9, 11]\nweights: [uniform, distance]\np: [1 (Manhattan), 2 (Euclidean)]",
            "20 kombinasi",
            f"k={tuning['KNN']['best_params']['model__n_neighbors']}, p={tuning['KNN']['best_params']['model__p']}, weights='{tuning['KNN']['best_params']['model__weights']}'",
        ],
        [
            "Decision Tree\n(Pipeline: DT, tanpa scaler)",
            "max_depth: [5, 8, 12, None]\nmin_samples_leaf: [1, 2, 4]\ncriterion: [gini, entropy]",
            "24 kombinasi",
            f"criterion='{tuning['Decision Tree']['best_params']['model__criterion']}', max_depth={tuning['Decision Tree']['best_params']['model__max_depth']}, min_leaf={tuning['Decision Tree']['best_params']['model__min_samples_leaf']}",
        ],
        [
            "Logistic Regression\n(Pipeline: Scaler → LR)",
            "C: [0.01, 0.1, 1, 10, 100]\nmax_iter = 3000",
            "5 kombinasi",
            f"C={tuning['Logistic Regression']['best_params']['model__C']} (max_iter=3000)",
        ],
    ]
    _add_table(
        sl,
        ["Model & Pipeline", "Ruang Hyperparameter GridSearch", "Kandidat", "Parameter Terbaik (Training 1.760)"],
        tun_rows,
        x=1.12,
        y=4.92,
        w=17.8,
        h=3.95,
        col_widths=[3.9, 6.2, 2.2, 5.5],
        font_size=15,
    )
    _add_textbox(
        sl,
        "Protokol anti-leakage: Data testing (440 baris = 20/tanaman) dikunci selama tuning dan seleksi model. Pilihan pemenang dicatat di results/selection_before_test.json sebelum evaluasi holdout test dilakukan, dan model final tidak di-refit pada seluruh 2.200 baris.",
        1.12,
        9.12,
        17.8,
        1.1,
        font_name="Garet",
        size=16,
        color=MUTED_LIGHT,
    )
    _set_notes(sl, "Bagian H (2/2): Jelaskan pembagian data, alasan Nested CV (menilai seluruh proses tuning tanpa bias seleksi), ruang GridSearch, dan parameter terbaik hasil training.")

    # ── SLIDE 12: I. Evaluasi & Perbandingan Model (Template Slide 3 + Table) ─
    sl = _clone_slide(prs, 2)
    _remove_by_names(sl, {f"TextBox {k}" for k in range(15, 27)})
    _add_badge_and_footer(sl, "Bagian I • Evaluasi & Perbandingan Model", 12, total_pages, light_footer=True)
    _format_slide3_header(
        sl,
        "EVALUASI & PERBANDINGAN",
        "Perbandingan adil 3 model pada Nested CV (1.760 train) dan Holdout Test (440 test, 20/kelas)",
    )
    eval_rows = []
    for m in ["Logistic Regression", "Decision Tree", "KNN"]:
        cr = cv_map.loc[m]
        tr = test_map.loc[m]
        tag = "  ★ AKTIF" if m == best else ""
        eval_rows.append(
            [
                f"{m}{tag}",
                f"{cr.cv_f1_macro_mean:.6f} ± {cr.cv_f1_macro_std:.4f}",
                f"{tr.accuracy:.4f} ({int(tr.n_correct)}/440)",
                f"{tr.precision_macro:.4f}",
                f"{tr.recall_macro:.4f}",
                f"{tr.f1_macro:.4f}",
                f"{cr.cv_gap:.4f}",
            ]
        )
    _add_table(
        sl,
        ["Model", "Nested CV Macro-F1 ± SD", "Test Accuracy", "Precision Macro", "Recall Macro", "F1-Score Macro", "Gap CV"],
        eval_rows,
        x=1.12,
        y=4.92,
        w=17.8,
        h=3.65,
        col_widths=[3.6, 3.6, 2.7, 2.1, 2.0, 2.1, 1.7],
        font_size=15,
    )
    _add_textbox(
        sl,
        "• Mengapa Macro-F1? Semua 22 jenis tanaman mendapat bobot penilaian setara, sehingga kesalahan pada satu jenis tanaman langsung terdeteksi.\n"
        "• Seluruh angka berasal dari eksekusi nyata train.py dan terverifikasi identik terhadap hasil prediksi tersimpan di results/test_predictions.csv.\n"
        "• Confusion matrix 22×22 dan classification report lengkap tiap kelas tersedia di Lampiran & aplikasi TunasMatch.",
        1.12,
        8.82,
        17.8,
        1.5,
        font_name="Garet",
        size=16,
        color=WHITE,
        space_after=4,
    )
    _set_notes(sl, "Bagian I: Paparkan perbandingan lengkap seluruh metrik wajib klasifikasi (Accuracy, Precision, Recall, F1-Score macro, Nested CV macro-F1, dan Gap CV).")

    # ── SLIDE 13: J. Pemilihan Model Terbaik (Template Slide 6 + Plot) ────────
    sl = _clone_slide(prs, 5)
    _remove_by_names(sl, {"Freeform 17"})
    _add_badge_and_footer(sl, "Bagian J • Pemilihan Model Terbaik", 13, total_pages, light_footer=False)
    diff_lr_dt = abs(float(cv_map.loc["Logistic Regression", "cv_f1_macro_mean"]) - float(cv_map.loc["Decision Tree", "cv_f1_macro_mean"]))
    _format_slide6_left(
        sl,
        "PEMILIHAN MODEL TERBAIK",
        "Logistic Regression dipilih dari validasi, bukan test accuracy tertinggi",
        f"• Aturan seleksi (pra-test): Mean outer Nested CV Macro-F1 tertinggi.\n"
        f"• Hasil validasi: Logistic Regression tertinggi ({cv_map.loc['Logistic Regression', 'cv_f1_macro_mean']:.6f}) sekaligus memiliki gap train–validasi terkecil ({cv_map.loc['Logistic Regression', 'cv_gap']:.4f}).\n"
        f"• Kejujuran ilmiah: Selisih LR dan DT sangat tipis ({diff_lr_dt:.6f}, praktis seri) — tidak diklaim signifikan secara statistik.\n"
        f"• Mengapa tidak ganti ke Decision Tree walau test accuracy DT lebih tinggi (98,64% vs 96,82%)? Mengganti pemenang setelah melihat data uji melanggar prinsip anti-leakage (test bukan alat seleksi model).",
        body_size=18.5,
    )
    _add_image_card(sl, ROOT / "plots/perbandingan_cv.png", 10.25, 2.25, 9.15, 7.75)
    _set_notes(sl, "Bagian J: Ini poin kunci yang dinilai dosen — pemilihan model didasarkan pada protokol validasi dan analisis gap overfitting, bukan sekadar mengambil test accuracy tertinggi.")

    # ── SLIDE 14: Analisis Model: Performa Terendah & Kesalahan (Tpl Slide 6) ─
    sl = _clone_slide(prs, 5)
    _remove_by_names(sl, {"Freeform 17"})
    _add_badge_and_footer(sl, "Analisis Model • Kesalahan & Performa Terendah", 14, total_pages, light_footer=False)
    _format_slide6_left(
        sl,
        "ANALISIS KESALAHAN MODEL",
        "Penyebab performa terendah & pasangan tanaman tertukar",
        "• Model terendah di Nested CV: KNN (0,9824). Penyebab: metode jarak sensitif terhadap bobot skala antarfitur di ruang 7D dan tumpang tindih lokal (6 rice→jute, 4 mothbeans→lentil di test).\n"
        "• Model terendah di Holdout Test: Logistic Regression (96,82%; 14 salah dari 440). Penyebab: batas keputusan linear kurang lentur pada sedikit sampel perbatasan non-linear dibanding aturan pohon DT.\n"
        "• Pola kesalahan model aktif (LR): Terkonsentrasi pada rice → jute (5 kasus) dan lentil → mothbeans (3 kasus), sesuai temuan EDA kemiripan fitur NPK & kelembapan.",
        body_size=18.5,
    )
    _add_image_card(sl, ROOT / "plots/pasangan_tertukar.png", 10.25, 2.25, 9.15, 7.75)
    _set_notes(sl, "Memenuhi Panduan Bagian 10 poin 02 & 04: pembahasan eksplisit model performa terendah, penyebabnya, serta analisis kesalahan prediksi per pasangan kelas.")

    # ── SLIDE 15: Analisis Fitur, Overfitting & Scaling (Tpl Slide 6 + 2 Plots)
    sl = _clone_slide(prs, 5)
    _remove_by_names(sl, {"Freeform 17"})
    _add_badge_and_footer(sl, "Analisis Model • Fitur, Overfitting & Scaling", 15, total_pages, light_footer=False)
    top3_imp = ", ".join(f"{r.feature} ({r.importance:.2f})" for r in imp.head(3).itertuples())
    knn_un = float(sc[(sc.model == "KNN") & (sc.scaling == False)].cv_f1_macro_mean.iloc[0])
    knn_sc = float(sc[(sc.model == "KNN") & (sc.scaling == True)].cv_f1_macro_mean.iloc[0])
    _format_slide6_left(
        sl,
        "FITUR, OVERFIT & SCALING",
        "Pengaruh fitur, cek overfitting/underfitting, & ablation scaling",
        f"• Pengaruh fitur (DT impurity importance): 3 teratas adalah {top3_imp}. Catatan: bukan penjelasan lokal LR dan bukan klaim biologis bahwa pH tidak penting.\n"
        f"• Cek overfitting/underfitting: Tidak ada underfitting berat. Gap train–CV kecil (LR 0,0081; DT 0,0122; KNN 0,0176). Train=1,0 pada KNN distance wajar karena titik bertetangga dengan dirinya sendiri.\n"
        f"• Ablation scaling (CV training, k=5 / depth=8): Pada split ini, scaling KNN k=5 justru menurunkan skor ({knn_un:.4f} → {knn_sc:.4f}); DT identik (0,8045). Dilaporkan jujur apa adanya.",
        body_size=18,
    )
    _add_image_card(sl, ROOT / "plots/feature_importance.png", 10.25, 2.18, 9.15, 3.85, pad=0.14)
    _add_image_card(sl, ROOT / "plots/train_cv_test.png", 10.25, 6.18, 9.15, 3.85, pad=0.14)
    _set_notes(sl, "Memenuhi Panduan Bagian 10 poin 03 & 05: analisis overfitting/underfitting (train vs nested CV vs test), feature importance Decision Tree, dan hasil jujur eksperimen scaling.")

    # ── SLIDE 16: K. Implementasi Aplikasi (Template Slide 5 - 3 Cards) ───────
    sl = _clone_slide(prs, 4)
    _add_badge_and_footer(sl, "Bagian K • Implementasi Aplikasi", 16, total_pages, light_footer=True)
    _format_slide5_header(
        sl,
        f"IMPLEMENTASI {APP_NAME.upper()}",
        "Arsitektur lokal: Python 3.14 · Streamlit · scikit-learn · joblib (tanpa training saat startup)",
    )
    _set_text(_find_shape(sl, "TextBox 32"), "01. INPUT", size=23, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER, space_after=0)
    _set_text(_find_shape(sl, "TextBox 33"), "02. PROSES", size=23, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER, space_after=0)
    _set_text(_find_shape(sl, "TextBox 34"), "03. OUTPUT", size=23, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER, space_after=0)
    _set_text(
        _find_shape(sl, "TextBox 36"),
        "• Form interaktif 7 parameter lahan (N, P, K, suhu, kelembapan, pH, hujan) + preset contoh.\n• Upload batch CSV (maks. 5 MB / 10.000 baris) + template kosong.",
        size=17,
        color=WHITE,
        align=PP_ALIGN.LEFT,
        space_after=6,
    )
    _set_text(
        _find_shape(sl, "TextBox 37"),
        "• Verifikasi SHA-256 models/crop_bundle.joblib.\n• validate_inputs() menolak NaN, teks, negatif, pH∉[0,14], humidity∉[0,100].\n• Inferensi lewat Pipeline & LabelEncoder terlatih.",
        size=16.5,
        color=WHITE,
        align=PP_ALIGN.LEFT,
        space_after=6,
    )
    _set_text(
        _find_shape(sl, "TextBox 38"),
        "• Rekomendasi tanaman utama & top-3 skor kelas + grafik bar.\n• Profil min/median/max training & peringatan out-of-range.\n• Unduh hasil CSV + menu Evaluasi & Kenali Dataset.",
        size=16.5,
        color=WHITE,
        align=PP_ALIGN.LEFT,
        space_after=6,
    )
    _add_textbox(
        sl,
        "Arsitektur kode modular: crop_core.py (kontrak validasi & inferensi)  →  models/crop_bundle.joblib (pipeline + encoder + profil)  →  app.py (antarmuka web 4 menu Streamlit).",
        1.12,
        9.78,
        17.8,
        0.58,
        font_name="Garet Bold",
        size=15.5,
        bold=True,
        color=MUTED_LIGHT,
    )
    _set_notes(sl, "Bagian K: Mencakup semua komponen wajib panduan — arsitektur aplikasi, teknologi (Python, Streamlit, scikit-learn, joblib), input, proses validasi+pipeline, dan output.")

    # ── SLIDE 17: L. Demo Project (Template Slide 6 + Screenshot TunasMatch) ──
    sl = _clone_slide(prs, 5)
    _remove_by_names(sl, {"Freeform 17"})
    _add_badge_and_footer(sl, "Bagian L • Demo Project", 17, total_pages, light_footer=False)
    _format_slide6_left(
        sl,
        f"DEMO APLIKASI {APP_NAME.upper()}",
        "Aplikasi web dijalankan langsung (streamlit run app.py)",
        "Alur demonstrasi langsung:\n"
        "1. Prediksi 1 Lahan: Muat contoh Padi atau isi 7 angka → klik 'Lihat rekomendasi' → tampil kelas utama (97,9%), top-3 skor, dan profil training.\n"
        "2. Prediksi Batch CSV: Unggah examples/contoh_batch.csv (22 lahan) → proses → unduh hasil_batch.csv.\n"
        "3. Uji Validasi Error: Unggah examples/contoh_tidak_valid.csv (humidity=120%) → aplikasi menolak dengan pesan jelas.\n"
        "4. Evaluasi & Dataset: Tampilkan perbandingan CV/test, confusion matrix, dan grafik EDA.\n"
        "Teruji otomatis: 13 pengecekan browser (desktop & mobile) lulus tanpa error.",
        title_size=54,
        body_size=17.8,
    )
    _add_image_card(sl, ROOT / "assets/screenshot_prediksi.png", 10.18, 2.15, 9.25, 7.9, pad=0.18)
    _set_notes(sl, "Bagian L: Screenshot berasal dari aplikasi TunasMatch yang benar-benar dijalankan. Saat presentasi dan video demo, jalankan aplikasi secara langsung melalui JALANKAN_APLIKASI.bat atau streamlit run app.py.")

    # ── SLIDE 18: M. Kesimpulan (Template Slide 9 - Narrative + 3 Pill Badges)
    sl = _clone_slide(prs, 8)
    _add_badge_and_footer(sl, "Bagian M • Kesimpulan", 18, total_pages, light_footer=False)
    t = _find_shape(sl, "TextBox 31")
    _set_box(t, left=1.12, top=1.42, width=12.0, height=1.7)
    _set_text(t, "KESIMPULAN", size=70, bold=True, color=DARK_GREEN, space_after=0)
    sub = _find_shape(sl, "TextBox 26")
    _set_box(sub, left=1.12, top=4.62, width=14.8, height=0.72)
    _set_text(sub, "Model tervalidasi tanpa leakage & aplikasi TunasMatch siap dijalankan", size=26, bold=True, color=WHITE, space_after=0)
    body = _find_shape(sl, "TextBox 27")
    _set_box(body, left=1.12, top=5.48, width=14.9, height=2.85)
    _set_text(
        body,
        "• Ketiga algoritma (KNN, Decision Tree, Logistic Regression) berhasil mengklasifikasikan 22 jenis tanaman dari 7 parameter tanah & iklim pada 2.200 data seimbang.\n"
        "• Logistic Regression dipilih secara sah melalui Nested CV Macro-F1 (0,985205; gap terkecil 0,0081), mencapai akurasi uji 96,82% (426/440 benar) tanpa memilih ulang dari data test.\n"
        "• Aplikasi web TunasMatch berjalan lokal secara reproduktif (input tunggal, batch CSV, validasi ketat, & audit evaluasi) sebagai prototipe edukasi berbasis pola data.",
        size=18.5,
        bold=False,
        color=WHITE,
        line_spacing=1.16,
        space_after=5,
    )
    _set_text(_find_shape(sl, "TextBox 28"), "NESTED CV ANTI-LEAKAGE", size=18.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER, space_after=0)
    _set_text(_find_shape(sl, "TextBox 29"), "MODEL AKTIF: LOGISTIC REG.", size=18.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER, space_after=0)
    _set_text(_find_shape(sl, "TextBox 30"), "APLIKASI TUNASMATCH SIAP", size=18.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER, space_after=0)
    _set_notes(sl, "Bagian M: Rangkum hasil utama proyek secara ringkas, tegas, dan tetap memisahkan performa benchmark dataset dari jaminan budidaya lapangan.")

    # ── SLIDE 19: N. Keterbatasan & Pengembangan (Template Slide 5 - 3 Cards) ─
    sl = _clone_slide(prs, 4)
    _add_badge_and_footer(sl, "Bagian N • Keterbatasan & Pengembangan", 19, total_pages, light_footer=True)
    _format_slide5_header(
        sl,
        "KETERBATASAN & PENGEMBANGAN",
        "Evaluasi kritis terhadap batas dataset, model, dan aplikasi serta rencana lanjutan",
        title_size=56,
    )
    _set_text(_find_shape(sl, "TextBox 32"), "Keterbatasan Dataset", size=22, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER, space_after=0)
    _set_text(_find_shape(sl, "TextBox 33"), "Keterbatasan Model", size=22, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER, space_after=0)
    _set_text(_find_shape(sl, "TextBox 34"), "Keterbatasan Aplikasi", size=22, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER, space_after=0)
    _set_text(
        _find_shape(sl, "TextBox 36"),
        "• Konteks India & augmentasi (R1); belum divalidasi di lahan Indonesia.\n• Satuan NPK & periode hujan belum diaudit.\n• Tidak memuat faktor varietas, hama, tekstur tanah, atau harga.",
        size=16.5,
        color=WHITE,
        align=PP_ALIGN.LEFT,
        space_after=5,
    )
    _set_text(
        _find_shape(sl, "TextBox 37"),
        "• Probabilitas predict_proba belum dikalibrasi (bukan peluang panen).\n• Terbatas pada 22 kelas label.\n• Split acak belum menguji generalisasi antar-wilayah atau musim baru.",
        size=16.5,
        color=WHITE,
        align=PP_ALIGN.LEFT,
        space_after=5,
    )
    _set_text(
        _find_shape(sl, "TextBox 38"),
        "• Saat ini berjalan lokal (deployment online bersifat opsional).\n• Belum terhubung sensor IoT/database histori lahan.\n• Belum memiliki detektor out-of-distribution (OOD) otomatis.",
        size=16.5,
        color=WHITE,
        align=PP_ALIGN.LEFT,
        space_after=5,
    )
    dev_box = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.12), Inches(9.70), Inches(17.75), Inches(0.80))
    dev_box.adjustments[0] = 0.08
    dev_box.fill.solid()
    dev_box.fill.fore_color.rgb = DARK_GREEN
    dev_box.line.color.rgb = ACCENT_GREEN
    dev_box.line.width = Pt(1.5)
    _add_textbox(
        sl,
        "Pengembangan Selanjutnya: Kumpulkan dataset lahan Indonesia ber-ID lokasi & waktu, verifikasi satuan bersama ahli agronomi, terapkan group/time split + kalibrasi probabilitas, integrasi sensor IoT, dan deployment cloud.",
        1.32,
        9.80,
        17.35,
        0.62,
        font_name="Garet",
        size=15,
        color=WHITE,
        space_after=0,
    )
    _set_notes(sl, "Bagian N: Memenuhi 4 komponen wajib panduan secara eksplisit — keterbatasan dataset, keterbatasan model, keterbatasan aplikasi, dan rencana pengembangan selanjutnya.")

    # ── SLIDE 20: O. Pembagian Tugas (Template Slide 5 - 3 Member Cards) ──────
    sl = _clone_slide(prs, 4)
    _add_badge_and_footer(sl, "Bagian O • Pembagian Tugas", 20, total_pages, light_footer=True)
    _format_slide5_header(
        sl,
        "PEMBAGIAN TUGAS KELOMPOK",
        f"{group_name} ({kelas}) — Seluruh anggota memahami keseluruhan alur ML, kode, dan evaluasi",
        title_size=58,
    )
    pill_boxes = ["TextBox 32", "TextBox 33", "TextBox 34"]
    body_boxes = ["TextBox 36", "TextBox 37", "TextBox 38"]
    detailed_tasks = [
        f"NIM: {members[0]['nim']}\n• Audit dataset & manifest sumber.\n• Penyusunan 5 jurnal referensi & tabel studi literatur.\n• Analisis EDA, visualisasi, & keputusan preprocessing anti-leakage.",
        f"NIM: {members[1]['nim']}\n• Pengembangan pipeline KNN, Decision Tree, & Logistic Regression.\n• Eksekusi Nested CV, GridSearch tuning, & ablation scaling.\n• Evaluasi metrik, confusion matrix, & analisis error.",
        f"NIM: {members[2]['nim']}\n• Implementasi aplikasi Streamlit {APP_NAME} (form, batch CSV, validasi).\n• Pengujian otomatis (pytest & browser) serta dokumentasi.\n• Penyusunan PPT laporan & video demo aplikasi.",
    ]
    for pb, bb, m, detail in zip(pill_boxes, body_boxes, members, detailed_tasks):
        _set_text(_find_shape(sl, pb), m["name"], size=19.5, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER, space_after=0)
        b_sh = _find_shape(sl, bb)
        _set_box(b_sh, top=7.12, height=2.25)
        _set_text(b_sh, detail, size=15.5, color=WHITE, align=PP_ALIGN.LEFT, line_spacing=1.14, space_after=4)
    _add_textbox(
        sl,
        "Catatan integritas: AI digunakan sebagai alat bantu belajar & debugging; seluruh eksperimen dieksekusi nyata dan dipertanggungjawabkan bersama pada sesi tanya jawab individu.",
        1.12,
        9.78,
        17.75,
        0.55,
        font_name="Garet",
        size=15,
        color=MUTED_LIGHT,
    )
    _set_notes(sl, "Bagian O: Kontribusi nyata 3 anggota sesuai identitas asli, disertai komitmen pemahaman lintas-tugas untuk tanya jawab individu.")

    # ── SLIDE 21: Lampiran - Confusion Matrix & Daftar Pustaka DOI (Tpl 6) ────
    sl = _clone_slide(prs, 5)
    _remove_by_names(sl, {"Freeform 17"})
    _add_badge_and_footer(sl, "Lampiran • Confusion Matrix & Daftar Pustaka", 21, total_pages, light_footer=False)
    ref_lines = "\n".join(
        f"[{r['id']}] {r['authors'].split(';')[0]} et al. ({r['year']}). {r['journal'].split(',')[0]}.\n      https://doi.org/{r['doi']}"
        for r in REFERENCES
    )
    _format_slide6_left(
        sl,
        "LAMPIRAN: CM & REFERENSI",
        "5 Jurnal Referensi DOI & Confusion Matrix 22×22 (LR)",
        ref_lines,
        title_size=54,
        sub_size=20.5,
        body_size=15.5,
    )
    _add_image_card(sl, ROOT / f"plots/confusion_{best.replace(' ', '_')}.png", 10.25, 2.15, 9.15, 7.9, pad=0.16)
    _set_notes(sl, "Lampiran: 5 referensi jurnal ilmiah dengan DOI terverifikasi Crossref (metadata & artikel di folder references/) serta Confusion Matrix 22x22 lengkap untuk model aktif Logistic Regression.")

    # ── SLIDE 22: Penutup / Terima Kasih (Template Slide 10) ──────────────────
    sl = _clone_slide(prs, 9)
    _set_text(_find_shape(sl, "TextBox 42"), f"{kelas.upper()}", size=19, bold=True, color=WHITE, line_spacing=1.08, space_after=0)
    _set_text(_find_shape(sl, "TextBox 39"), "TERIMA KASIH", size=80, bold=True, color=DARK_GREEN, space_after=0)
    _set_text(
        _find_shape(sl, "TextBox 38"),
        f"Terima kasih atas perhatiannya.\nKami siap mendemonstrasikan aplikasi {APP_NAME} dan menerima pertanyaan.",
        size=23,
        bold=False,
        color=WHITE,
        line_spacing=1.18,
    )
    _set_text(_find_shape(sl, "TextBox 35"), "Kelompok & Aplikasi", size=20, color=WHITE, space_after=0)
    tb37 = _find_shape(sl, "TextBox 37")
    _set_box(tb37, width=7.2)
    _set_text(tb37, f"{group_name}  —  {APP_NAME}", size=23, bold=True, color=WHITE, space_after=0)
    _set_text(_find_shape(sl, "TextBox 34"), "Kelas / Mata Kuliah", size=20, color=WHITE, space_after=0)
    tb36 = _find_shape(sl, "TextBox 36")
    _set_box(tb36, width=7.6)
    _set_text(tb36, f"{kelas}", size=23, bold=True, color=WHITE, space_after=0)
    _set_notes(sl, f"Penutup: {group_name} ({kelas}) — {APP_NAME}. Siap demo langsung aplikasi dan sesi tanya jawab individu.")

    _delete_first_n_slides(prs, n_orig)
    prs.save(OUTPUT_PATH)
    return OUTPUT_PATH


if __name__ == "__main__":
    summary = read_json(ROOT / "results/summary.json")
    cfg = read_json(ROOT / "group_config.json")
    cv_df = pd.read_csv(ROOT / "results/cv_comparison.csv")
    test_df = pd.read_csv(ROOT / "results/test_comparison.csv")
    out = build_ppt_from_template(summary, cfg, cv_df, test_df)
    print("PPT dibangun dari template:", out)
