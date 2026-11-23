# Opsional: PDF cadangan dan render slide untuk pemeriksaan visual.
# Memerlukan PowerPoint/Word desktop. Tidak mematikan aplikasi pengguna lain.
param([switch]$ExportWord)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$ppt = $null
$deck = $null
$word = $null
$doc = $null
try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $deck = $ppt.Presentations.Open((Join-Path $root 'presentation\Laporan_Proyek_Tanaman.pptx'), $true, $false, $false)
    $deck.SaveAs((Join-Path $root 'presentation\Laporan_Proyek_Tanaman.pdf'), 32)
    $render = Join-Path $root 'presentation\render'
    New-Item -ItemType Directory -Path $render -Force | Out-Null
    Get-ChildItem -Path $render -Filter 'slide_*.png' -ErrorAction SilentlyContinue | Remove-Item -Force
    for ($i = 1; $i -le $deck.Slides.Count; $i++) {
        $deck.Slides.Item($i).Export((Join-Path $render ("slide_{0:D2}.png" -f $i)), 'PNG', 1600, 900)
    }
    Write-Output "PowerPoint slides exported: $($deck.Slides.Count)"
}
finally {
    if ($null -ne $deck) { $deck.Close() }
    if (($null -ne $ppt) -and ($ppt.Presentations.Count -eq 0)) { $ppt.Quit() }
}
if ($ExportWord) { try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open((Join-Path $root 'docs\Penjelasan_Tanaman_Bahasa_Sederhana.docx'), $false, $true)
    $doc.ExportAsFixedFormat((Join-Path $root 'docs\Penjelasan_Tanaman_Bahasa_Sederhana.pdf'), 17)
    Write-Output 'Word PDF exported.'
}
finally {
    if ($null -ne $doc) { $doc.Close(0) }
    if (($null -ne $word) -and ($word.Documents.Count -eq 0)) { $word.Quit() }
} }
