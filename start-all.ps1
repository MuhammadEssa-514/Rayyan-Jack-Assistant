#!/usr/bin/env pwsh
# ============================================================
# Jack AI - Start All Services Script
# Usage: .\start-all.ps1
# ============================================================

$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       🤖 Jack AI - Multi Launcher        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 1. Ollama Service
Write-Host "🚀 Launching Ollama AI Engine..." -ForegroundColor Yellow
Start-Process "powershell" -ArgumentList "-NoExit -Command Write-Host '=== Ollama AI Service ===' -ForegroundColor Green; ollama serve"

# 2. Server
Write-Host "🚀 Launching Core Node.js Server..." -ForegroundColor Yellow
$serverDir = Join-Path $PROJECT_ROOT "server"
Start-Process "powershell" -ArgumentList "-NoExit -Command Set-Location '$serverDir'; Write-Host '=== Jack Core Server ===' -ForegroundColor Green; npm run dev"

# 3. Next.js Dashboard
Write-Host "🚀 Launching Web Dashboard..." -ForegroundColor Yellow
$dashDir = Join-Path $PROJECT_ROOT "dashboard"
Start-Process "powershell" -ArgumentList "-NoExit -Command Set-Location '$dashDir'; Write-Host '=== Jack Web Dashboard ===' -ForegroundColor Green; npm run dev"

# 4. Windows Agent
Write-Host "🚀 Launching Windows Automation Agent..." -ForegroundColor Yellow
$agentDir = Join-Path $PROJECT_ROOT "windows-agent"
$python = "C:\Users\Com Plus\AppData\Local\Programs\Python\Python311\python.exe"
if (-not (Test-Path $python)) { $python = "python" }
Start-Process "powershell" -ArgumentList "-NoExit -Command Set-Location '$agentDir'; Write-Host '=== Windows Automation Agent ===' -ForegroundColor Green; & '$python' main.py"

# 5. Voice Engine
Write-Host "🚀 Launching Voice Engine (Microphone + Whisper + TTS)..." -ForegroundColor Yellow
$voiceDir = Join-Path $PROJECT_ROOT "voice-engine"
Start-Process "powershell" -ArgumentList "-NoExit -Command Set-Location '$voiceDir'; Write-Host '=== Voice Engine ===' -ForegroundColor Green; & '$python' main.py"

Write-Host ""
Write-Host "✅ All 5 Jack AI components launched in separate processes!" -ForegroundColor Green
Write-Host "  • Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  • Server:    http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
