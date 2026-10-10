$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$npm = "C:\Program Files\nodejs\npm.cmd"

if (-not (Test-Path $python)) {
    throw "Missing .venv. Create it and install backend/requirements.txt first."
}
if (-not (Test-Path $npm)) {
    throw "Node.js was not found at $npm."
}

Start-Process -FilePath $python -WorkingDirectory (Join-Path $root "backend") `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"
Start-Process -FilePath $npm -WorkingDirectory (Join-Path $root "frontend") `
    -ArgumentList "run", "dev"

Write-Host "ResolveFlow API: http://localhost:8000/docs"
Write-Host "ResolveFlow UI:  http://localhost:3000"
