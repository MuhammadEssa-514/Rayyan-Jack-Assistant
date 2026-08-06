#!/usr/bin/env pwsh
# ============================================================
# Jack AI - Complete Setup Script
# Run this once after cloning the project
# Usage: .\setup.ps1
# ============================================================

$PYTHON = "C:\Users\Com Plus\AppData\Local\Programs\Python\Python311\python.exe"
$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║    Jack AI — Full Setup Script           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ─── Helper functions ───────────────────────────────────────
function Step($n, $msg) {
    Write-Host ""
    Write-Host "[$n] $msg" -ForegroundColor Yellow
    Write-Host ("─" * 50) -ForegroundColor DarkGray
}

function OK($msg)   { Write-Host "  ✅ $msg" -ForegroundColor Green }
function WARN($msg) { Write-Host "  ⚠️  $msg" -ForegroundColor Yellow }
function ERR($msg)  { Write-Host "  ❌ $msg" -ForegroundColor Red }

# ─── 1. Check Python ────────────────────────────────────────
Step 1 "Checking Python 3.11..."
if (Test-Path $PYTHON) {
    $ver = & $PYTHON --version 2>&1
    OK "Python found: $ver"
} else {
    ERR "Python not found at $PYTHON"
    ERR "Please install Python 3.11 first: winget install Python.Python.3.11"
    exit 1
}

# ─── 2. Windows Agent Dependencies ──────────────────────────
Step 2 "Installing Windows Agent Python packages..."
$agentDir = Join-Path $PROJECT_ROOT "windows-agent"
& $PYTHON -m pip install -r "$agentDir\requirements.txt" --quiet
if ($LASTEXITCODE -eq 0) { OK "Windows Agent packages installed" }
else { WARN "Some packages may have failed - check manually" }

# ─── 3. Playwright Chromium Browser ─────────────────────────
Step 3 "Installing Playwright Chromium browser..."
& $PYTHON -m playwright install chromium
if ($LASTEXITCODE -eq 0) { OK "Playwright Chromium installed" }
else { WARN "Playwright browser install failed - browser automation won't work" }

# ─── 4. Voice Engine Dependencies ───────────────────────────
Step 4 "Installing Voice Engine Python packages..."
$voiceDir = Join-Path $PROJECT_ROOT "voice-engine"
& $PYTHON -m pip install -r "$voiceDir\requirements.txt" --quiet
if ($LASTEXITCODE -eq 0) { OK "Voice Engine packages installed" }
else { WARN "Some Voice Engine packages failed - voice features may be limited" }

# ─── 5. Download Piper TTS Models ───────────────────────────
Step 5 "Downloading Piper TTS voice models..."
$modelsDir = Join-Path $voiceDir "models"
New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null

$urduModel = Join-Path $modelsDir "ur_PK-usman-medium.onnx"
$urduConfig = Join-Path $modelsDir "ur_PK-usman-medium.onnx.json"

if (-not (Test-Path $urduModel)) {
    Write-Host "  Downloading Urdu TTS model (~70MB)..." -ForegroundColor Gray
    $modelUrl = "https://huggingface.co/rhasspy/piper-voices/resolve/main/ur/ur_PK/usman/medium/ur_PK-usman-medium.onnx"
    $configUrl = "https://huggingface.co/rhasspy/piper-voices/resolve/main/ur/ur_PK/usman/medium/ur_PK-usman-medium.onnx.json"
    try {
        Invoke-WebRequest -Uri $modelUrl -OutFile $urduModel -UseBasicParsing
        Invoke-WebRequest -Uri $configUrl -OutFile $urduConfig -UseBasicParsing
        OK "Urdu TTS model downloaded"
    } catch {
        WARN "Failed to download Urdu model: $_"
        WARN "Falling back to English TTS"
        # Download English fallback
        $enModel = Join-Path $modelsDir "en_US-lessac-medium.onnx"
        $enConfig = Join-Path $modelsDir "en_US-lessac-medium.onnx.json"
        $enModelUrl = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
        $enConfigUrl = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
        try {
            Invoke-WebRequest -Uri $enModelUrl -OutFile $enModel -UseBasicParsing
            Invoke-WebRequest -Uri $enConfigUrl -OutFile $enConfig -UseBasicParsing
            OK "English TTS model downloaded (fallback)"
        } catch {
            ERR "TTS model download failed. Voice responses will use system TTS."
        }
    }
} else {
    OK "Urdu TTS model already exists"
}

# ─── 6. Server Node.js dependencies ─────────────────────────
Step 6 "Installing Server Node.js packages..."
$serverDir = Join-Path $PROJECT_ROOT "server"
if (-not (Test-Path (Join-Path $serverDir "node_modules"))) {
    Set-Location $serverDir
    npm install --silent
    if ($LASTEXITCODE -eq 0) { OK "Server packages installed" }
    else { WARN "npm install failed for server" }
    Set-Location $PROJECT_ROOT
} else {
    OK "Server packages already installed"
}

# ─── 7. Dashboard Node.js dependencies ──────────────────────
Step 7 "Installing Dashboard packages..."
$dashDir = Join-Path $PROJECT_ROOT "dashboard"
if (-not (Test-Path (Join-Path $dashDir "node_modules"))) {
    Set-Location $dashDir
    npm install --silent
    if ($LASTEXITCODE -eq 0) { OK "Dashboard packages installed" }
    else { WARN "npm install failed for dashboard" }
    Set-Location $PROJECT_ROOT
} else {
    OK "Dashboard packages already installed"
}

# ─── 8. Check Ollama ────────────────────────────────────────
Step 8 "Checking Ollama AI Engine..."
$ollamaPath = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaPath) {
    OK "Ollama found at: $($ollamaPath.Source)"
    Write-Host "  Starting ollama service..." -ForegroundColor Gray
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep 3
    Write-Host "  Pulling qwen2.5:7b model (this will take 10-30 min depending on internet)..." -ForegroundColor Gray
    Write-Host "  Model size: ~4.7GB" -ForegroundColor DarkGray
    ollama pull qwen2.5:7b
    if ($LASTEXITCODE -eq 0) { OK "qwen2.5:7b model ready" }
    else { WARN "Model pull failed - run manually: ollama pull qwen2.5:7b" }
} else {
    WARN "Ollama not found in PATH yet"
    WARN "If just installed, restart terminal and run: ollama pull qwen2.5:7b"
}

# ─── 9. Create Screenshots directory ────────────────────────
Step 9 "Creating required directories..."
New-Item -ItemType Directory -Force -Path (Join-Path $agentDir "screenshots") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $voiceDir "logs") | Out-Null
OK "Directories created"

# ─── Summary ────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║         Setup Complete! 🎉               ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps to start Jack AI:" -ForegroundColor Cyan
Write-Host "  1. Terminal 1: cd server  && node src/index.js" -ForegroundColor White
Write-Host "  2. Terminal 2: cd dashboard && npm run dev" -ForegroundColor White
Write-Host "  3. Terminal 3: ollama serve" -ForegroundColor White
Write-Host "  4. Terminal 4: cd windows-agent && python main.py" -ForegroundColor White
Write-Host "  5. Terminal 5: cd voice-engine  && python main.py  (optional)" -ForegroundColor White
Write-Host ""
Write-Host "  Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Server:    http://localhost:5000/api/health" -ForegroundColor Cyan
Write-Host ""
