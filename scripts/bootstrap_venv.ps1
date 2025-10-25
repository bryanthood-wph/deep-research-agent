$ErrorActionPreference = "Stop"
try { Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force } catch {}
$pylist = & py -0p
if ($pylist -match "Python311") {
    $ver = "3.11"
} else {
    $ver = "3.10"
}
if (!(Test-Path .\.venv\Scripts\Activate.ps1)) { & py -$ver -m venv .venv }
. .\.venv\Scripts\Activate.ps1
python -m pip install -U pip wheel
pip install -r requirements.txt
python scripts/sanity.py
Write-Host "Venv ready on Python $ver"

