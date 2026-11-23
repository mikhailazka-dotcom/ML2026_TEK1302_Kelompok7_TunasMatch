"""Uji kontrak, eksperimen dan UI; tidak bergantung pada internet."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crop_core import FEATURES, ROOT, load_bundle, load_dataset, predict_frame, range_warnings, read_json, sha256, validate_inputs


@pytest.fixture(scope="module")
def bundle(): return load_bundle()


@pytest.fixture
def example(): return pd.read_csv(ROOT / "examples/contoh_batch.csv").head(1)


def test_source_and_distribution():
    df=load_dataset()
    assert df.shape==(2200,8)
    assert (df.label.value_counts()==100).all()
    assert not df.isna().any().any()
    assert not df.duplicated().any()
    assert sha256(ROOT / "Crop_recommendation.csv")==read_json(ROOT / "data/source_manifest.json")["sha256"]


def test_split_and_fold_integrity():
    df=load_dataset(); split=read_json(ROOT / "results/split_indices.json")
    a,b=set(split["train"]),set(split["test"])
    assert not a & b
    assert a | b==set(range(2200))
    assert len(a)==1760 and len(b)==440
    assert (df.iloc[split["train"]].label.value_counts()==80).all()
    assert (df.iloc[split["test"]].label.value_counts()==20).all()
    oof=pd.read_csv(ROOT / "results/oof_predictions.csv")
    for _,g in oof.groupby("model"):
        assert len(g)==1760 and g.row_id.nunique()==1760
        assert set(g.row_id)==a
        assert set(g.fold)=={1,2,3,4,5}


def test_selection_not_test():
    cv=pd.read_csv(ROOT / "results/cv_comparison.csv")
    choice=read_json(ROOT / "results/selection_before_test.json")
    assert not choice["test_used_for_selection"]
    winner=cv.sort_values(["cv_f1_macro_mean","cv_f1_macro_std","model"],ascending=[False,True,True]).iloc[0].model
    assert winner==choice["selected_model"]==read_json(ROOT / "results/summary.json")["selected_model"]


def test_metrics_match_saved_predictions(bundle):
    df=load_dataset(); split=read_json(ROOT / "results/split_indices.json")
    te=df.iloc[split["test"]]
    out,probs=predict_frame(te[FEATURES],bundle)
    summary=read_json(ROOT / "results/summary.json")
    assert accuracy_score(te.label,out.rekomendasi)==pytest.approx(summary["selected_test"]["accuracy"])
    assert f1_score(te.label,out.rekomendasi,average="macro")==pytest.approx(summary["selected_test"]["f1_macro"])
    saved=pd.read_csv(ROOT / "results/test_predictions.csv")
    saved=saved[saved.model==bundle["selected_model"]]
    assert list(out.rekomendasi)==list(saved.predicted)
    assert np.allclose(probs.sum(axis=1),1)
    assert (probs.to_numpy()>=0).all()
    assert list(bundle["pipeline"].feature_names_in_)==FEATURES


def test_scaler_uses_only_training(bundle):
    if "scaler" not in bundle["pipeline"].named_steps: pytest.skip("Pemenang tanpa scaler")
    df=load_dataset(); ids=read_json(ROOT / "results/split_indices.json")["train"]
    scaler=bundle["pipeline"].named_steps["scaler"]
    assert int(scaler.n_samples_seen_)==1760
    assert np.allclose(scaler.mean_, df.iloc[ids][FEATURES].mean().to_numpy())


def test_column_order_and_extra_columns(example,bundle):
    normal,_=predict_frame(example,bundle)
    shuffled=example[list(reversed(FEATURES))].copy(); shuffled["label"]="not_a_model_input"
    result,_=predict_frame(shuffled,bundle)
    pd.testing.assert_frame_equal(normal,result)


@pytest.mark.parametrize("column,value",[("N",-1),("rainfall",-1),("humidity",101),("humidity",-1),("ph",15),("ph",-1),("K",np.nan),("P",np.inf),("temperature",-274)])
def test_bad_numbers_rejected(example,column,value):
    example[column]=value
    with pytest.raises(ValueError): validate_inputs(example)


def test_text_rejected(example):
    example["N"]="abc"
    with pytest.raises(ValueError):validate_inputs(example)


def test_incomplete_and_empty_rejected(example):
    with pytest.raises(ValueError):validate_inputs(example.drop(columns="ph"))
    with pytest.raises(ValueError):validate_inputs(example.iloc[:0])
    bad=pd.concat([example,example[["N"]]],axis=1)
    with pytest.raises(ValueError):validate_inputs(bad)


def test_zero_and_out_of_range(example,bundle):
    example["N"]=0
    assert validate_inputs(example).N.iloc[0]==0
    example["N"]=1000
    validate_inputs(example)
    assert "N" in range_warnings(example,bundle["bounds"])


def test_all_three_reports_complete():
    reports=read_json(ROOT / "results/classification_reports.json")
    labels=set(load_dataset().label)
    assert len(reports)==3
    for report in reports.values():
        assert labels <= set(report)
        assert all(report[label]["support"]==20 for label in labels)


def test_streamlit_single_pages_reset():
    from streamlit.testing.v1 import AppTest
    at=AppTest.from_file(str(ROOT / "app.py"),default_timeout=60).run()
    assert not at.exception
    assert any('class="app-brandbar"' in x.value and 'TunasMatch' in x.value for x in at.markdown)
    next(b for b in at.button if b.label=="Lihat rekomendasi").click().run()
    assert not at.exception
    assert any("Hasil rekomendasi" in x.value for x in at.markdown)
    assert any("score-fill" in x.value for x in at.markdown)
    assert any('class="profile-table"' in x.value for x in at.markdown)
    at.number_input(key="input_rainfall").set_value(70.).run()
    assert any("Input berubah" in x.value for x in at.info)
    next(b for b in at.button if b.label=="Reset contoh padi").click().run()
    assert "single_result" not in at.session_state
    for page in ["Evaluasi model","Kenali dataset","Panduan","Rekomendasi"]:
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, page
