"""Browser nyata: uji alur, screenshot, rekam demo tanpa narasi/perkenalan."""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import imageio_ffmpeg
from playwright.sync_api import sync_playwright, TimeoutError as BrowserTimeout

from crop_core import APP_NAME, ROOT, write_json


def browser_path():
    for p in [Path(os.environ.get("PROGRAMFILES(X86)",""))/"Microsoft/Edge/Application/msedge.exe",Path(os.environ.get("PROGRAMFILES",""))/"Google/Chrome/Application/chrome.exe"]:
        if p.exists():return str(p)
    return None


def main():
    checks=[]
    for f in ["assets","video","results"]:(ROOT/f).mkdir(exist_ok=True)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0));port=sock.getsockname()[1]
    url=f"http://127.0.0.1:{port}"
    temp_parent=Path(os.environ.get("LOCALAPPDATA",str(ROOT)))/"Temp/opencode"
    temp_parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="crop_demo_",dir=temp_parent) as td, (ROOT / "results/streamlit_capture.log").open("w",encoding="utf-8") as log:
        process=subprocess.Popen([sys.executable,"-m","streamlit","run",str(ROOT/"app.py"),"--server.headless","true","--server.address","127.0.0.1","--server.port",str(port),"--browser.gatherUsageStats","false"],cwd=ROOT,stdout=log,stderr=log)
        try:
            for _ in range(100):
                if process.poll() is not None:raise RuntimeError("Streamlit berhenti; lihat streamlit_capture.log")
                try:
                    if urlopen(url+"/_stcore/health",timeout=1).status==200:break
                except OSError:time.sleep(.2)
            else:raise TimeoutError("Streamlit tidak siap")
            with sync_playwright() as pw:
                browser=pw.chromium.launch(executable_path=browser_path(),headless=True)
                context=browser.new_context(viewport={"width":1440,"height":1050},record_video_dir=td,record_video_size={"width":1440,"height":1050})
                page=context.new_page();page_errors=[]
                page.set_default_timeout(60000)
                page.on("pageerror",lambda e:page_errors.append(str(e)))
                page.goto(url,wait_until="networkidle")
                try:
                    page.get_by_role("heading",name="Kenali kondisi lahanmu",exact=True).wait_for(timeout=20000)
                except BrowserTimeout:
                    # Windows/Edge kadang memutus koneksi awal WebSocket.
                    page.reload(wait_until="networkidle")
                    page.get_by_role("heading",name="Kenali kondisi lahanmu",exact=True).wait_for()
                page.wait_for_function("name => document.title === name",arg=APP_NAME)
                checks.append("startup_brand")
                def caption(text):
                    page.evaluate('''text => {let el=document.getElementById('demo-caption');if(!el){el=document.createElement('div');el.id='demo-caption';document.body.appendChild(el)}el.textContent=text;Object.assign(el.style,{position:'fixed',bottom:'15px',left:'330px',right:'25px',padding:'14px 20px',background:'#173d30f0',color:'white',fontSize:'17px',fontFamily:'sans-serif',borderRadius:'12px',zIndex:999999,pointerEvents:'none'})}''',text)
                def wait(seconds=3):page.wait_for_timeout(seconds*1000)
                def screenshot(name):
                    page.evaluate("document.getElementById('demo-caption')?.remove()")
                    page.screenshot(path=str(ROOT / "assets" / name),full_page=True)
                assert page.locator('.brand-name').inner_text() == APP_NAME
                header = page.locator('.app-brandbar').bounding_box()
                left = page.locator('.st-key-measurement_card').bounding_box()
                right = page.locator('.st-key-result_card').bounding_box()
                assert header and left and right
                assert right['x'] > left['x'] + left['width'], 'Kartu desktop harus berdampingan.'
                assert abs(left['y'] - right['y']) < 3, 'Kartu desktop harus sejajar.'
                checks.append('desktop_header_and_side_by_side_cards')
                # Tunggu widget native selesai dimuat, bukan hanya judul kartu.
                page.locator('[data-testid="stNumberInput"] input').nth(6).wait_for()
                page.get_by_role('button', name='Muat contoh', exact=True).wait_for()
                screenshot('screenshot_desktop_redesign.png')
                caption(f"{APP_NAME} — rekaman layar aplikasi nyata; bahan demo tanpa narasi/perkenalan.");wait(4)
                page.get_by_role("button",name="Lihat rekomendasi",exact=True).click()
                page.get_by_role("heading",name="Hasil rekomendasi",exact=True).wait_for()
                page.get_by_role("heading",name="Hasil rekomendasi",exact=True).evaluate("el => el.scrollIntoView({block:'start'})")
                page.locator(".score-fill").first.wait_for()
                page.locator(".profile-table table").wait_for()
                caption("1. Tujuh input diproses pipeline terlatih. Label dan skor berasal dari model, bukan hasil yang diatur manual.");wait(5)
                screenshot("screenshot_prediksi.png");checks.append("single_prediction")
                caption("Skor bukan peluang panen. Profil training bukan kondisi ideal atau resep pemupukan.")
                page.get_by_text("Ini ringkasan contoh berlabel",exact=False).scroll_into_view_if_needed();wait(4)
                page.get_by_role("tab",name="Banyak lahan / CSV",exact=True).click()
                page.locator('input[type="file"]').set_input_files(str(ROOT / "examples/contoh_batch.csv"))
                page.get_by_role("button",name="Proses CSV",exact=True).wait_for()
                wait(1)
                page.get_by_role("button",name="Proses CSV",exact=True).click()
                page.get_by_text("Selesai memprediksi 22 baris.",exact=True).wait_for()
                caption("2. Upload CSV dengan tujuh kolom wajib. Dua puluh dua contoh ini berasal dari training, bukan evaluasi tambahan.");wait(5)
                screenshot("screenshot_batch.png");checks.append("batch_22_rows")
                page.locator('input[type="file"]').set_input_files(str(ROOT / "examples/contoh_tidak_valid.csv"))
                page.get_by_role("button",name="Remove contoh_tidak_valid.csv",exact=True).wait_for();wait(1)
                page.get_by_role("button",name="Proses CSV",exact=True).click()
                page.get_by_text("Kelembapan harus antara 0 dan 100%.",exact=False).wait_for()
                caption("Input fisik tidak valid ditolak; aplikasi tidak diam-diam mengarang pengukuran yang hilang.");wait(4)
                checks.append("invalid_humidity_rejected")
                page.get_by_text("Evaluasi model",exact=True).first.click()
                page.get_by_role("heading",name="Evaluasi model",exact=True).wait_for()
                caption("3. Pemenang dipilih dari nested CV training. DT tertinggi di test tidak dipakai mengganti model aktif.");wait(5)
                screenshot("screenshot_evaluasi.png");checks.append("evaluation_page")
                page.get_by_role("tab",name="Kesalahan prediksi",exact=True).click()
                caption("Confusion matrix 22 x 22: baris aktual, kolom prediksi. Kesalahan per kelas tetap perlu dibahas.");wait(5)
                screenshot("screenshot_confusion.png");checks.append("confusion_page")
                page.get_by_role("tab",name="Fitur & pohon",exact=True).click()
                caption("Importance milik Decision Tree. Ini bukan penyebab hasil panen dan bukan penjelasan lokal LR.");wait(4)
                checks.append("feature_tree_page")
                page.get_by_text("Kenali dataset",exact=True).first.click()
                page.get_by_role("heading",name="Kenali dataset",exact=True).wait_for()
                caption("4. Dataset seimbang, lengkap, dan dirujuk dalam konteks India. Definisi satuan/periode perlu dipastikan.");wait(4)
                screenshot("screenshot_dataset.png");checks.append("dataset_page")
                page.get_by_text("Panduan",exact=True).first.click()
                page.get_by_role("heading",name="Panduan",exact=True).wait_for();wait(3)
                checks.append("guide_page")
                page.get_by_text("Rekomendasi",exact=True).first.click()
                page.get_by_role("tab",name="Satu lahan",exact=True).click()
                page.get_by_role("button",name="Reset contoh padi",exact=True).click()
                page.get_by_text("Belum ada prediksi.",exact=False).wait_for()
                checks.append("reset_clears_results")
                caption("Lengkapi identitas, perkenalan dan narasi kelompok sebelum mengumpulkan video maksimal 7 menit.");wait(4)
                screenshot("screenshot_beranda.png")
                page.set_viewport_size({"width":390,"height":844});wait(2)
                page.get_by_role("heading",name="Kenali kondisi lahanmu",exact=True).wait_for()
                screenshot("screenshot_mobile.png")
                overflow=page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2")
                assert not overflow,"Halaman melebar di layar mobile"
                header=page.locator('.app-brandbar').bounding_box()
                subtitle=page.locator('.brand-subtitle').bounding_box()
                assert header and subtitle and subtitle['x']+subtitle['width'] <= 390
                assert subtitle['y']+subtitle['height'] <= header['y']+header['height']
                left=page.locator('.st-key-measurement_card').bounding_box()
                right=page.locator('.st-key-result_card').bounding_box()
                assert left and right and right['y'] > left['y']+left['height']
                checks.append('mobile_header_and_stacked_cards')
                checks.append("mobile_no_horizontal_overflow")
                assert not page_errors,page_errors
                video=page.video
                context.close();source=Path(video.path());browser.close()
            ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
            target=ROOT / "video/demo_aplikasi.mp4"
            subprocess.run([ffmpeg,"-y","-i",str(source),"-an","-c:v","libx264","-crf","25","-pix_fmt","yuv420p","-movflags","+faststart",str(target)],check=True,capture_output=True)
            probe=subprocess.run([ffmpeg,"-i",str(target)],capture_output=True,text=True)
            duration=[line.strip() for line in probe.stderr.splitlines() if "Duration:" in line]
            write_json(ROOT / "results/browser_tests.json", {"executed_utc":datetime.now(timezone.utc).isoformat(),"checks_passed":checks,"page_errors":page_errors,"video":"video/demo_aplikasi.mp4","note":"Rekaman layar nyata tanpa narasi/perkenalan; bukan video final kelompok.","duration_metadata":duration})
            print("Browser checks:",len(checks));print("Video:",target);print(*duration,sep="\n")
        finally:
            process.terminate()
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)


if __name__ == "__main__":main()
