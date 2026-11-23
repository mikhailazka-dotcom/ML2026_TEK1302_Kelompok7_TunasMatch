"""Opsional: simpan metadata terverifikasi dan PDF open access bila server mengizinkan."""
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import json

from crop_core import ROOT, sha256, write_json
from references import REFERENCES


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "TaniPintar-Educational-Project/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def main():
    folder = ROOT / "references"
    folder.mkdir(exist_ok=True)
    logs = []
    for ref in REFERENCES:
        r = {"id": ref["id"], "doi": ref["doi"], "checked_utc": datetime.now(timezone.utc).isoformat()}
        try:
            raw = fetch("https://api.crossref.org/works/" + ref["doi"])
            metadata = json.loads(raw)["message"]
            write_json(folder / f"{ref['id']}_metadata_crossref.json", metadata)
            r["metadata"] = "Crossref berhasil; judul/penulis/tahun bisa diperiksa pada JSON."
        except Exception as exc:
            r["metadata"] = str(exc)
        try:
            # R1 juga tersedia di repositori open-access Europe PMC.
            url = "https://europepmc.org/articles/PMC9412477?pdf=render" if ref["id"] == "R1" else ref["pdf"]
            raw = fetch(url)
            if not raw.startswith(b"%PDF"):
                raise ValueError("Respons bukan PDF; tidak disimpan sebagai artikel palsu.")
            path = folder / f"{ref['id']}_artikel.pdf"
            path.write_bytes(raw)
            r["pdf"] = str(path.relative_to(ROOT))
            r["sha256"] = sha256(path)
            r["download_url"] = url
        except Exception as exc:
            r["pdf_status"] = "Belum tersimpan: " + str(exc)
            r["read_online"] = ref["url"]
            if ref["id"] == "R1":
                try:
                    import xml.etree.ElementTree as ET
                    xml_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9412477/fullTextXML"
                    raw_xml = fetch(xml_url)
                    (folder / "R1_teks_lengkap.xml").write_bytes(raw_xml)
                    tree = ET.fromstring(raw_xml)
                    text = "\n\n".join(" ".join(el.itertext()) for el in tree.iter() if el.tag in {"article-title", "title", "p"})
                    (folder / "R1_teks_lengkap.txt").write_text(text, encoding="utf-8")
                    r["full_text"] = "references/R1_teks_lengkap.txt"
                    r["full_text_url"] = xml_url
                except Exception as text_exc:
                    r["full_text_status"] = str(text_exc)
        print(ref["id"], r.get("pdf", r.get("pdf_status")), flush=True)
        logs.append(r)
    write_json(folder / "verification_log.json", logs)


if __name__ == "__main__": main()
