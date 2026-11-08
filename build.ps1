# Единая сборка Infinity Xray для PowerShell. Параметры передаются build.py.
$ErrorActionPreference = 'Stop'
$buildPath = Join-Path $PSScriptRoot 'build.py'
& python $buildPath @args
exit $LASTEXITCODE
