param(
  [string]$Prefix = "",
  [string]$RepoUrl = "",
  [string]$Branch = "",
  [string]$FromLocal = "",
  [switch]$Force,
  [switch]$Check,
  [switch]$NoStart
)

$ErrorActionPreference = "Stop"

function Resolve-FalsiflowPath([string]$PathText) {
  $expanded = [Environment]::ExpandEnvironmentVariables($PathText)
  return [System.IO.Path]::GetFullPath($expanded)
}

function Require-Command([string]$Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $Name"
  }
}

if (-not $Prefix) {
  if ($env:FALSIFLOW_HOME) {
    $Prefix = $env:FALSIFLOW_HOME
  } else {
    $Prefix = Join-Path $HOME ".falsiflow"
  }
}
if (-not $RepoUrl) {
  $RepoUrl = if ($env:FALSIFLOW_REPO_URL) { $env:FALSIFLOW_REPO_URL } else { "https://github.com/falsiflow/falsiflow.git" }
}
if (-not $Branch) {
  $Branch = if ($env:FALSIFLOW_BRANCH) { $env:FALSIFLOW_BRANCH } else { "main" }
}

Require-Command python
if (-not $FromLocal) {
  Require-Command git
}

$PrefixAbs = Resolve-FalsiflowPath $Prefix
$SourceDir = Join-Path $PrefixAbs "source"
$VenvDir = Join-Path $PrefixAbs "venv"
$AppDir = Join-Path $PrefixAbs "app"
$IsWin = ($env:OS -eq "Windows_NT") -or ($PSVersionTable.PSEdition -eq "Desktop")
New-Item -ItemType Directory -Force -Path $PrefixAbs | Out-Null

if ($FromLocal) {
  $FromLocalAbs = Resolve-FalsiflowPath $FromLocal
  if (-not (Test-Path (Join-Path $FromLocalAbs "pyproject.toml")) -or -not (Test-Path (Join-Path $FromLocalAbs "falsiflow"))) {
    throw "--FromLocal must point to a Falsiflow checkout."
  }
  if ($Force -and (Test-Path $SourceDir)) {
    Remove-Item -Recurse -Force $SourceDir
  }
  if (Test-Path $SourceDir) {
    Write-Host "Using existing source checkout: $SourceDir"
  } else {
    New-Item -ItemType Directory -Force -Path $SourceDir | Out-Null
    Get-ChildItem -Force $FromLocalAbs |
      Where-Object { $_.Name -notin @(".git", "build", "dist", "__pycache__") -and $_.Name -notlike "*.egg-info" } |
      Copy-Item -Destination $SourceDir -Recurse -Force
  }
} else {
  if ($Force -and (Test-Path $SourceDir)) {
    Remove-Item -Recurse -Force $SourceDir
  }
  if (Test-Path (Join-Path $SourceDir ".git")) {
    Write-Host "Updating existing source checkout: $SourceDir"
    git -C $SourceDir fetch --quiet origin $Branch
    git -C $SourceDir checkout --quiet $Branch
    git -C $SourceDir pull --ff-only --quiet origin $Branch
  } elseif (Test-Path $SourceDir) {
    throw "Source directory already exists and is not a git checkout: $SourceDir. Use -Force to replace it."
  } else {
    Write-Host "Cloning Falsiflow from $RepoUrl"
    git clone --branch $Branch --depth 1 $RepoUrl $SourceDir
  }
}

if (-not (Test-Path $VenvDir)) {
  python -m venv $VenvDir
}

$PythonExe = if ($IsWin) { Join-Path $VenvDir "Scripts/python.exe" } else { Join-Path $VenvDir "bin/python" }
$FalsiflowExe = if ($IsWin) { Join-Path $VenvDir "Scripts/falsiflow.exe" } else { Join-Path $VenvDir "bin/falsiflow" }

& $PythonExe -m pip install --upgrade pip | Out-Null
& $PythonExe -m pip install -e $SourceDir | Out-Null

Write-Host "Falsiflow installed."
Write-Host ""
Write-Host "Install directory: $PrefixAbs"
Write-Host "Launcher: $FalsiflowExe"
Write-Host ""
Write-Host "Next commands:"
Write-Host "  $FalsiflowExe start"
Write-Host "  $FalsiflowExe start --check --json"

if ($NoStart) {
  exit 0
}

if ($Check) {
  & $FalsiflowExe start --out-dir $AppDir --check --json
} else {
  & $FalsiflowExe start --out-dir $AppDir
}
