"""Eksekusi notebook audit; tidak menimpa model utama."""
import time
import nbformat
from nbclient import NotebookClient
from crop_core import ROOT, sha256, write_json


def main():
    start=time.perf_counter()
    target=ROOT / "PROJEK_TANAMAN.ipynb"
    template=ROOT / "docs/Template_Notebook_Tanpa_Output.ipynb"
    before=sha256(ROOT / "models/crop_bundle.joblib")
    nb=nbformat.read(template,as_version=4)
    client=NotebookClient(nb,timeout=1200,kernel_name="python3",resources={"metadata":{"path":str(ROOT)}})
    client.execute()
    assert sha256(ROOT / "models/crop_bundle.joblib")==before, "Model utama berubah saat eksekusi notebook."
    nbformat.write(nb,target)
    codes=[c for c in nb.cells if c.cell_type=="code"]
    errors=[o for c in codes for o in c.get("outputs",[]) if o.output_type=="error"]
    write_json(ROOT / "results/notebook_execution.json", {"code_cells":len(codes),"executed":sum(c.execution_count is not None for c in codes),"errors":len(errors),"main_model_unchanged":True,"elapsed_seconds":round(time.perf_counter()-start,2)})
    print("Notebook selesai:",len(codes),"cell kode;",len(errors),"error; model utama tidak berubah.")


if __name__ == "__main__":main()
