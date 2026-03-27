# Package Detector (PD) Windows Installer (PowerShell)
# ---------------------------------------------------

$INSTALL_DIR = Join-Path $HOME ".package-detector"
$VENV_DIR = Join-Path $INSTALL_DIR "venv"
$SRC_DIR = Join-Path $INSTALL_DIR "src"
$BIN_DIR = Join-Path $INSTALL_DIR "bin"

# Ensure directories exist
New-Item -ItemType Directory -Force -Path $SRC_DIR
New-Item -ItemType Directory -Force -Path $BIN_DIR

Write-Host "🛡️ Installing Package Detector (PD) for Windows..." -ForegroundColor Cyan

# 1. Copy source files
Write-Host "📂 Copying source files..."
Copy-Item -Path ".\*" -Destination $SRC_DIR -Recurse -Force -Exclude ".git", "venv", ".venv", "__pycache__"

# 2. Setup Virtual Environment
Write-Host "🔧 Setting up virtual environment..."
python -m venv $VENV_DIR

# 3. Install Dependencies
Write-Host "📦 Installing dependencies (this may take a few minutes)..."
$PIP_PATH = Join-Path $VENV_DIR "Scripts\pip.exe"
& $PIP_PATH install -r "$SRC_DIR\requirements.txt"
& $PIP_PATH install typer questionary
& $PIP_PATH install -e $SRC_DIR

# 4. Create Batch Wrapper
Write-Host "🛠️ Creating pd.cmd wrapper..."
$BATCH_FILE = "$BIN_DIR\pd.cmd"
$PYTHON_EXE = Join-Path $VENV_DIR "Scripts\python.exe"
$GUARD_PY = Join-Path $SRC_DIR "pg\guard.py"

$BATCH_CONTENT = @"
@echo off
set PYTHONPATH=$SRC_DIR;%PYTHONPATH%
"$PYTHON_EXE" "$GUARD_PY" %*
"@

$BATCH_CONTENT | Out-File -FilePath $BATCH_FILE -Encoding ascii

Write-Host "================================================================" -ForegroundColor Green
Write-Host "✅ Package Detector (PD) installed successfully!" -ForegroundColor Green
Write-Host "📍 Location: $INSTALL_DIR"
Write-Host "📍 Command:  $BATCH_FILE"
Write-Host ""
Write-Host "⚠️  ACTION REQUIRED: Add '$BIN_DIR' to your System PATH manually."
Write-Host "================================================================"
Write-Host "🚀 Try running: pd --help"
