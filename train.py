"""Eksperimen reproduktif. Nested CV memilih model; test bukan alat tuning."""
from __future__ import annotations

import argparse
import importlib.metadata
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_validate, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree

from crop_core import FEATURES, ROOT, SEED, SOURCE_URL, TITLE, load_dataset, sha256, write_json

sns.set_theme(style="whitegrid", palette="crest", font_scale=0.95)
plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 160, "axes.titleweight": "bold"})


def candidates():
    return {
        "KNN": (Pipeline([("scaler", StandardScaler()), ("model", KNeighborsClassifier())]),
                {"model__n_neighbors": [3, 5, 7, 9, 11], "model__weights": ["uniform", "distance"], "model__p": [1, 2]}),
        "Decision Tree": (Pipeline([("model", DecisionTreeClassifier(random_state=SEED))]),
                          {"model__max_depth": [5, 8, 12, None], "model__min_samples_leaf": [1, 2, 4], "model__criterion": ["gini", "entropy"]}),
        "Logistic Regression": (Pipeline([("scaler", StandardScaler()), ("model", LogisticRegression(max_iter=3000))]),
                                {"model__C": [0.01, 0.1, 1, 10, 100]}),
    }


def search_for(pipe, grid, cv):
    return GridSearchCV(pipe, grid, scoring="f1_macro", cv=cv, refit=True,
                        n_jobs=1, error_score="raise", return_train_score=True)


def metrics(y, p):
    return {"accuracy": float(accuracy_score(y, p)), "precision_macro": float(precision_score(y, p, average="macro", zero_division=0)),
            "recall_macro": float(recall_score(y, p, average="macro", zero_division=0)), "f1_macro": float(f1_score(y, p, average="macro", zero_division=0))}


def save_fig(path):
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close()


def eda(df, tr, out):
    plots = out / "plots"
    res = out / "results"
    df.describe().T.to_csv(res / "descriptive_source.csv")
    tr[FEATURES].describe().T.to_csv(res / "descriptive_train.csv")
    tr.groupby("label")[FEATURES].mean().to_csv(res / "crop_means_train.csv")
    df.label.value_counts().sort_index().rename_axis("label").to_csv(res / "class_counts.csv")
    fig, ax = plt.subplots(figsize=(11, 5))
    df.label.value_counts().sort_index().plot.bar(ax=ax, color="#27835d")
    ax.set(title="Distribusi sumber: 100 contoh untuk setiap tanaman", xlabel="Tanaman", ylabel="Jumlah contoh")
    save_fig(plots / "distribusi_kelas.png")
    fig, axs = plt.subplots(2, 4, figsize=(14, 7))
    for f, ax in zip(FEATURES, axs.flat):
        sns.histplot(tr[f], kde=True, ax=ax, color="#27835d")
        ax.set_title(f)
    axs.flat[-1].axis("off")
    fig.suptitle("Distribusi tujuh fitur — training saja", y=1.02)
    save_fig(plots / "histogram.png")
    fig, axs = plt.subplots(2, 4, figsize=(14, 6))
    outliers = []
    for f, ax in zip(FEATURES, axs.flat):
        sns.boxplot(x=tr[f], ax=ax, color="#b8d8ba")
        q1, q3 = tr[f].quantile([.25, .75]); iqr = q3-q1
        low, high = float(q1-1.5*iqr), float(q3+1.5*iqr)
        outliers.append({"feature": f, "lower": low, "upper": high, "n_flagged": int((~tr[f].between(low, high)).sum())})
    axs.flat[-1].axis("off")
    fig.suptitle("Boxplot training: nilai ekstrem tidak otomatis salah", y=1.02)
    save_fig(plots / "boxplot.png")
    pd.DataFrame(outliers).to_csv(res / "outliers_iqr_train.csv", index=False)
    plt.figure(figsize=(8, 6))
    sns.heatmap(tr[FEATURES].corr(), annot=True, fmt=".2f", cmap="BrBG", vmin=-1, vmax=1)
    plt.title("Korelasi fitur numerik — bukan sebab-akibat")
    save_fig(plots / "korelasi.png")
    fig, axs = plt.subplots(1, 2, figsize=(13, 5))
    subset = tr[tr.label.isin(["rice", "jute", "maize"])]
    sns.scatterplot(data=subset, x="rainfall", y="humidity", hue="label", ax=axs[0])
    axs[0].set_title("Padi, jute, jagung: hujan & kelembapan")
    subset = tr[tr.label.isin(["mothbeans", "lentil", "blackgram", "pigeonpeas"])]
    sns.scatterplot(data=subset, x="P", y="humidity", hue="label", ax=axs[1])
    axs[1].set_title("Kacang-kacangan: sebagian pola bertumpang tindih")
    save_fig(plots / "scatter_kemiripan.png")
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.boxplot(data=tr, x="label", y="K", ax=ax, color="#b8d8ba")
    ax.tick_params(axis="x", rotation=65)
    ax.set_title("Kalium per kelas: nilai tinggi perlu dibaca dalam konteks kelas")
    save_fig(plots / "kalium_per_kelas.png")


def run_training(output_dir=None):
    out = Path(output_dir) if output_dir else ROOT
    for folder in ["models", "results", "plots", "examples", "data"]:
        (out / folder).mkdir(parents=True, exist_ok=True)
    res, plots = out / "results", out / "plots"
    start = time.perf_counter()
    df = load_dataset()
    ids = np.arange(len(df))
    train_ids, test_ids = train_test_split(ids, test_size=.2, random_state=SEED, stratify=df.label)
    tr, te = df.iloc[train_ids].copy(), df.iloc[test_ids].copy()
    x, xt = tr[FEATURES], te[FEATURES]
    encoder = LabelEncoder().fit(tr.label)
    y, yt = encoder.transform(tr.label), encoder.transform(te.label)
    labels = encoder.classes_.tolist()
    write_json(res / "split_indices.json", {"seed": SEED, "train": train_ids.tolist(), "test": test_ids.tolist()})
    write_json(res / "label_mapping.json", {str(i): label for i, label in enumerate(labels)})
    write_json(res / "data_profile.json", {"shape": list(df.shape), "dtypes": {c: str(t) for c,t in df.dtypes.items()},
        "missing": {c: int(v) for c,v in df.isna().sum().items()}, "duplicates": int(df.duplicated().sum()),
        "class_counts": {c: int(v) for c,v in df.label.value_counts().sort_index().items()},
        "train_counts": {c: int(v) for c,v in tr.label.value_counts().sort_index().items()},
        "test_counts": {c: int(v) for c,v in te.label.value_counts().sort_index().items()}})
    write_json(out / "data/source_manifest.json", {"filename": "Crop_recommendation.csv", "sha256": sha256(ROOT / "Crop_recommendation.csv"),
        "source_url": SOURCE_URL, "uploader_attribution": "Atharva Ingle", "origin": "CSV yang sudah disediakan pengguna; tidak diunduh ulang atau diganti",
        "provenance_caveat": "Tidak ada ID lahan, waktu, lokasi, protokol pengukuran, atau bukti hasil panen dalam CSV. Satuan NPK dan periode rainfall perlu dikonfirmasi ke pengelola sumber.",
        "license": "Periksa lisensi pada halaman Kaggle sebelum redistribusi publik; lisensi tidak disimpulkan dari CSV."})
    eda(df, tr, out)
    outer = StratifiedKFold(5, shuffle=True, random_state=SEED)
    inner = StratifiedKFold(3, shuffle=True, random_state=SEED + 1)
    final_cv = StratifiedKFold(5, shuffle=True, random_state=SEED + 2)
    rows, folds, oof, fitted, tuning = [], [], [], {}, {}
    # Kedua tingkat CV hanya melihat training. Outer menilai seluruh proses tuning.
    for name, (pipe, grid) in candidates().items():
        print(f"Nested CV: {name}", flush=True)
        model_folds = []
        for fold, (a, b) in enumerate(outer.split(x, y), 1):
            search = search_for(clone(pipe), grid, inner).fit(x.iloc[a], y[a])
            pred = search.predict(x.iloc[b])
            r = {"model": name, "fold": fold, "train_f1_macro": float(f1_score(y[a], search.predict(x.iloc[a]), average="macro")),
                 **metrics(y[b], pred), "best_params": str(search.best_params_)}
            folds.append(r); model_folds.append(r)
            for row_id, actual, guess in zip(train_ids[b], y[b], pred):
                oof.append({"model": name, "fold": fold, "row_id": int(row_id), "actual": labels[actual], "predicted": labels[guess], "correct": bool(actual == guess)})
        fs = pd.DataFrame(model_folds)
        rows.append({"model": name, "cv_f1_macro_mean": float(fs.f1_macro.mean()), "cv_f1_macro_std": float(fs.f1_macro.std(ddof=1)),
                     "cv_accuracy_mean": float(fs.accuracy.mean()), "cv_train_f1_mean": float(fs.train_f1_macro.mean()),
                     "cv_gap": float((fs.train_f1_macro - fs.f1_macro).mean())})
        final = search_for(clone(pipe), grid, final_cv).fit(x, y)
        tuning[name] = {"best_params": final.best_params_, "inner_training_cv_score": float(final.best_score_), "n_candidates": len(final.cv_results_["params"])}
        pd.DataFrame(final.cv_results_).to_csv(res / f"grid_{name.replace(' ', '_')}.csv", index=False)
        fitted[name] = final.best_estimator_
    cv_table = pd.DataFrame(rows).sort_values(["cv_f1_macro_mean", "cv_f1_macro_std", "model"], ascending=[False, True, True]).reset_index(drop=True)
    best = str(cv_table.iloc[0].model)
    cv_table.to_csv(res / "cv_comparison.csv", index=False)
    pd.DataFrame(folds).to_csv(res / "nested_cv_folds.csv", index=False)
    pd.DataFrame(oof).to_csv(res / "oof_predictions.csv", index=False)
    write_json(res / "tuning.json", tuning)
    write_json(res / "selection_before_test.json", {"selected_model": best, "criterion": "Mean outer nested-CV macro-F1 terbesar; tie: SD terkecil lalu nama alfabetis.",
        "selected_at_utc": datetime.now(timezone.utc).isoformat(), "test_used_for_selection": False, "seed": SEED,
        "protocol_note": "Baseline eksploratif seed=42 pernah diperiksa sebelum paket ini. Eksperimen final menggunakan seed=2026 yang ditetapkan di kode, tanpa mencoba seed demi skor. Tidak ada klaim blind/preregistered study."})
    # Ablation ditentukan di awal, CV training saja, tidak digunakan memilih ulang.
    scaling = []
    for name in ["KNN", "Decision Tree"]:
        base = KNeighborsClassifier(n_neighbors=5) if name == "KNN" else DecisionTreeClassifier(max_depth=8, random_state=SEED)
        for scaled in [False, True]:
            p = Pipeline(([('scaler', StandardScaler())] if scaled else []) + [("model", clone(base))])
            scores = cross_validate(p, x, y, cv=outer, scoring="f1_macro", n_jobs=1)
            scaling.append({"model": name, "scaling": scaled, "cv_f1_macro_mean": float(scores["test_score"].mean()), "cv_f1_macro_std": float(scores["test_score"].std(ddof=1)),
                            "setting": "k=5" if name == "KNN" else "max_depth=8"})
    pd.DataFrame(scaling).to_csv(res / "scaling_experiment.csv", index=False)
    test_rows, errors, predictions, reports, confusions = [], [], [], {}, []
    for name, pipe in fitted.items():
        p = pipe.predict(xt)
        row = {"model": name, "train_accuracy": float(accuracy_score(y, pipe.predict(x))),
               "train_f1_macro": float(f1_score(y, pipe.predict(x), average="macro")), **metrics(yt, p), "n_correct": int((yt == p).sum()), "n_test": len(te)}
        test_rows.append(row)
        reports[name] = classification_report(yt, p, labels=np.arange(len(labels)), target_names=labels, output_dict=True, zero_division=0)
        cm = confusion_matrix(yt, p, labels=np.arange(len(labels)))
        pd.DataFrame(cm, index=labels, columns=labels).to_csv(res / f"confusion_{name.replace(' ', '_')}.csv")
        plt.figure(figsize=(13, 11))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Greens", xticklabels=labels, yticklabels=labels, cbar=False, annot_kws={"size": 7})
        plt.title(f"{name} — test akhir (baris aktual, kolom prediksi)")
        plt.xlabel("Prediksi"); plt.ylabel("Aktual")
        save_fig(plots / f"confusion_{name.replace(' ', '_')}.png")
        for actual in range(len(labels)):
            for guess in range(len(labels)):
                if actual != guess and cm[actual, guess]:
                    confusions.append({"model": name, "actual": labels[actual], "predicted": labels[guess], "count": int(cm[actual, guess])})
        for i, actual, guess in zip(test_ids, yt, p):
            r = {"model": name, "row_id": int(i), "actual": labels[actual], "predicted": labels[guess], "correct": bool(actual == guess),
                 **{f: float(df.iloc[i][f]) for f in FEATURES}}
            predictions.append(r)
            if actual != guess: errors.append(r)
    test = pd.DataFrame(test_rows)
    test.to_csv(res / "test_comparison.csv", index=False)
    pd.DataFrame(predictions).to_csv(res / "test_predictions.csv", index=False)
    pd.DataFrame(errors, columns=["model", "row_id", "actual", "predicted", "correct"] + FEATURES).to_csv(res / "test_errors.csv", index=False)
    pairs = pd.DataFrame(confusions, columns=["model", "actual", "predicted", "count"]).sort_values(["count", "actual"], ascending=[False, True])
    pairs.to_csv(res / "confused_pairs.csv", index=False)
    write_json(res / "classification_reports.json", reports)
    importance = pd.DataFrame({"feature": FEATURES, "importance": fitted["Decision Tree"].named_steps["model"].feature_importances_}).sort_values("importance", ascending=False)
    importance.to_csv(res / "feature_importance_dt.csv", index=False)
    plt.figure(figsize=(8, 4)); sns.barplot(data=importance, x="importance", y="feature", color="#27835d")
    plt.title("Importance Decision Tree — bukan hubungan sebab-akibat")
    save_fig(plots / "feature_importance.png")
    fig, ax = plt.subplots(figsize=(21, 9))
    plot_tree(fitted["Decision Tree"].named_steps["model"], feature_names=FEATURES, class_names=labels, max_depth=3, filled=True, fontsize=8, ax=ax)
    ax.set_title("Empat tingkat pertama Decision Tree (pohon lengkap di berkas aturan)")
    save_fig(plots / "pohon_ringkas.png")
    (res / "aturan_decision_tree.txt").write_text("class angka mengikuti label_mapping.json\n" + export_text(fitted["Decision Tree"].named_steps["model"], feature_names=FEATURES, max_depth=100), encoding="utf-8")
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(cv_table.model, cv_table.cv_f1_macro_mean, yerr=cv_table.cv_f1_macro_std, capsize=5, color=["#27835d", "#e7af4f", "#7c9ca3"])
    ax.set(ylim=(0, 1.04), ylabel="Macro-F1", title="Nested CV training: mean ± SD (bukan confidence interval)")
    save_fig(plots / "perbandingan_cv.png")
    comparison = cv_table.merge(test, on="model")
    fig, ax = plt.subplots(figsize=(9, 4))
    comparison.set_index("model")[["train_f1_macro", "cv_f1_macro_mean", "f1_macro"]].rename(columns={"train_f1_macro":"Train", "cv_f1_macro_mean":"Nested CV", "f1_macro":"Test"}).plot.bar(ax=ax, rot=0)
    ax.set(ylim=(0, 1.05), ylabel="Macro-F1", title="Train, validasi, test: cari jarak skor yang terlalu besar")
    save_fig(plots / "train_cv_test.png")
    fig, ax = plt.subplots(figsize=(8, 4))
    sc = pd.DataFrame(scaling)
    sns.barplot(data=sc, x="model", y="cv_f1_macro_mean", hue="scaling", ax=ax)
    ax.set(ylim=(0, 1.05), title="Ablation scaling — setting tetap, CV training saja", ylabel="Macro-F1")
    save_fig(plots / "scaling.png")
    selected_pairs = pairs[pairs.model == best].head(10)
    fig, ax = plt.subplots(figsize=(9, 4))
    if len(selected_pairs):
        ax.barh([f"{r.actual} → {r.predicted}" for r in selected_pairs.itertuples()], selected_pairs["count"], color="#c98036")
        ax.invert_yaxis(); ax.set_xlabel("Jumlah kesalahan")
    else: ax.text(.1, .5, "Tidak ada kesalahan pada holdout ini.")
    ax.set_title(f"Pasangan kelas tertukar — {best}, test akhir")
    save_fig(plots / "pasangan_tertukar.png")
    bounds = {f: {"min": float(x[f].min()), "max": float(x[f].max())} for f in FEATURES}
    profiles = {label: {f: {"min": float(g[f].min()), "median": float(g[f].median()), "max": float(g[f].max())} for f in FEATURES} for label,g in tr.groupby("label")}
    bundle = {"pipeline": fitted[best], "encoder": encoder, "features": FEATURES, "selected_model": best, "bounds": bounds, "profiles": profiles, "seed": SEED}
    joblib.dump(bundle, out / "models/crop_bundle.joblib", compress=3)
    for name, pipe in fitted.items(): joblib.dump(pipe, out / f"models/{name.replace(' ', '_')}.joblib", compress=3)
    # Demonstrasi memakai contoh training, bukan test atau klaim pengujian baru.
    examples = tr.groupby("label", sort=True).head(1).sort_values("label")
    examples.to_csv(out / "examples/contoh_dengan_label.csv", index=False)
    examples[FEATURES].to_csv(out / "examples/contoh_batch.csv", index=False)
    examples[FEATURES].head(0).to_csv(out / "examples/template_input.csv", index=False)
    invalid = examples[FEATURES].head(1).copy(); invalid.loc[:, "humidity"] = 120
    invalid.to_csv(out / "examples/contoh_tidak_valid.csv", index=False)
    selected_test = test.set_index("model").loc[best].to_dict()
    summary = {"title": TITLE, "selected_model": best, "seed": SEED, "n_source": len(df), "n_train": len(tr), "n_test": len(te), "n_features": len(FEATURES), "n_classes": len(labels),
               "selected_cv": cv_table.iloc[0].to_dict(), "selected_test": selected_test, "best_params": tuning[best]["best_params"],
               "model_sha256": sha256(out / "models/crop_bundle.joblib"), "dataset_sha256": sha256(ROOT / "Crop_recommendation.csv"),
               "created_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": round(time.perf_counter()-start, 2),
               "python": platform.python_version(), "versions": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scikit-learn", "joblib", "matplotlib", "seaborn", "streamlit"]},
               "test_protocol": "Tidak dipakai tuning/pemilihan; model aplikasi sama dengan model yang dievaluasi, tidak refit seluruh sumber.",
               "probability_caveat": "Skor predict_proba belum dikalibrasi; bukan peluang sukses panen atau ukuran ketidakpastian yang terjamin."}
    write_json(res / "summary.json", summary)
    print(comparison.to_string(index=False), flush=True)
    print("Selected:", best, "| output:", out, flush=True)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    run_training(args.output_dir)
