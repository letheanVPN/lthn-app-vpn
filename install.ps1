#!/usr/bin/env pwsh
# Copyright 2018 the Deno authors. All rights reserved. MIT license.
# TODO(everyone): Keep this script simple and easily auditable.

$ErrorActionPreference = 'Stop'

if ($v) {
  $Version = "v${v}"
}
if ($args.Length -eq 1) {
  $Version = $args.Get(0)
}

$DenoInstall = $env:DENO_INSTALL
$BinDir = "$Home\Lethean"


$DenoZip = "$BinDir\lthn.zip"
$DenoExe = "$BinDir\lthn.exe"
$Target = 'windows'

# GitHub requires TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$DenoUri = "https://gitlab.com/lthn/projects/vpn/node/-/jobs/artifacts/dvpn-v2/download?job=${Target}"


if (!(Test-Path $BinDir)) {
  New-Item $BinDir -ItemType Directory | Out-Null
}

Invoke-WebRequest $DenoUri -OutFile $DenoZip -UseBasicParsing

if (Get-Command Expand-Archive -ErrorAction SilentlyContinue) {
  Expand-Archive $DenoZip -Destination $BinDir -Force
} else {
  if (Test-Path $DenoExe) {
    Remove-Item $DenoExe
  }
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [IO.Compression.ZipFile]::ExtractToDirectory($DenoZip, $BinDir)
}

Remove-Item $DenoZip

$User = [EnvironmentVariableTarget]::User
$Path = [Environment]::GetEnvironmentVariable('Path', $User)
if (!(";$Path;".ToLower() -like "*;$BinDir;*".ToLower())) {
  [Environment]::SetEnvironmentVariable('Path', "$Path;$BinDir", $User)
  $Env:Path += ";$BinDir"
}

Write-Output "Lethean CLI was installed successfully to $DenoExe"
Write-Output "Run 'lthn --help' to get started"
