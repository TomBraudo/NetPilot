# NetPilot Agent Build Script
# This script builds the agent into a standalone executable

Write-Host "=== NetPilot Agent Build Script ===" -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "package.json")) {
    Write-Host "Error: package.json not found. Please run this script from the agent directory." -ForegroundColor Red
    exit 1
}

Write-Host "Step 1: Cleaning previous build..." -ForegroundColor Yellow
if (Test-Path "dist") {
    Remove-Item "dist" -Recurse -Force
}

Write-Host "Step 2: Installing/updating dependencies..." -ForegroundColor Yellow
# Clean install to avoid native dependency issues
Remove-Item "node_modules" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "package-lock.json" -Force -ErrorAction SilentlyContinue

# Install dependencies with native module rebuild disabled
$env:npm_config_build_from_source = "false"
npm install --no-optional

# Workaround symlink privilege issue
$env:WIN_CODE_SIGN_VERSION = "2.2.0"  # older archive without symlinks
$env:USE_HARD_LINKS = "false"

Write-Host "Step 3: Building portable executable..." -ForegroundColor Yellow
# Use electron-builder with specific configuration to avoid native deps
npx electron-builder --win portable --config.nodeGypRebuild=false --config.buildDependenciesFromSource=false

if ($LASTEXITCODE -eq 0) {
    Write-Host "=== Build Successful! ===" -ForegroundColor Green
    # Locate portable exe
    $exe = Get-ChildItem "dist" -Filter "*-portable.exe" | Select-Object -First 1
    if (-not $exe) { Write-Host "Portable EXE not found" -ForegroundColor Red; exit 1 }
    # Copy .env into dist if it exists next to this script
    $envSource = Join-Path $PSScriptRoot '.env'
    $includeEnv = $false
    if (Test-Path $envSource) {
      Copy-Item $envSource (Join-Path "dist" '.env') -Force
      $includeEnv = $true
    } else {
      Write-Host "Warning: .env not found in agent folder; skipping copy" -ForegroundColor Yellow
    }

    # Create ZIP deliverable
    $zipName = "${($exe.BaseName)}.zip"
    $zipPath = Join-Path "dist" $zipName
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

    $pathsToZip = @($exe.FullName)
    if ($includeEnv) { $pathsToZip += (Join-Path "dist" '.env') }
    Compress-Archive -Path $pathsToZip -DestinationPath $zipPath

    Write-Host "Created deliverable: $zipName" -ForegroundColor Green
    Write-Host "Executable size: $([math]::Round($exe.Length/1MB,2)) MB" -ForegroundColor Cyan
} else {
    Write-Host "=== Build Failed! ===" -ForegroundColor Red
    Write-Host "Trying alternative build method..." -ForegroundColor Yellow
    
    # Try building without rebuilding native modules at all
    npx electron-builder --win portable --config.npmRebuild=false
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "=== Alternative Build Successful! ===" -ForegroundColor Green
        Get-ChildItem "dist\*.exe" | ForEach-Object {
            Write-Host "  -> $($_.Name) ($([math]::Round($_.Length/1MB, 2)) MB)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "Build failed. Please check the error messages above." -ForegroundColor Red
    }
}

# Clean up environment variable
Remove-Item Env:npm_config_build_from_source -ErrorAction SilentlyContinue
Remove-Item Env:WIN_CODE_SIGN_VERSION -ErrorAction SilentlyContinue
Remove-Item Env:USE_HARD_LINKS -ErrorAction SilentlyContinue 