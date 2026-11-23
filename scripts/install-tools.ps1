$ErrorActionPreference = 'Stop'
$toolRoot = Join-Path (Split-Path $PSScriptRoot -Parent) '.tools'
New-Item -ItemType Directory -Path $toolRoot -Force | Out-Null
function Install-VerifiedZip($baseUrl, $archive, $checksums, $destination) {
    $zipPath = Join-Path $toolRoot $archive
    Invoke-WebRequest "$baseUrl/$checksums" -OutFile (Join-Path $toolRoot $checksums)
    $line = Get-Content (Join-Path $toolRoot $checksums) | Where-Object { $_ -match "\s+$([regex]::Escape($archive))$" }
    if (-not $line) { throw "Checksum ausente: $archive" }
    Invoke-WebRequest "$baseUrl/$archive" -OutFile $zipPath
    $expected = ($line -split '\s+')[0]
    if ((Get-FileHash $zipPath -Algorithm SHA256).Hash.ToLower() -ne $expected.ToLower()) { throw "Checksum invalido: $archive" }
    Expand-Archive -LiteralPath $zipPath -DestinationPath $destination -Force
}
Install-VerifiedZip 'https://releases.hashicorp.com/terraform/1.17.2' 'terraform_1.17.2_windows_amd64.zip' 'terraform_1.17.2_SHA256SUMS' (Join-Path $toolRoot 'terraform')
$nodeBase = 'https://nodejs.org/dist/latest-v24.x'
$nodeSums = (Invoke-WebRequest "$nodeBase/SHASUMS256.txt").Content
$nodeArchive = (($nodeSums -split "`n" | Where-Object { $_ -match 'node-v24\..*-win-x64.zip$' }) -split '\s+')[-1].Trim()
if (-not $nodeArchive) { throw 'Node 24 LTS para Windows nao encontrado' }
Install-VerifiedZip $nodeBase $nodeArchive 'SHASUMS256.txt' $toolRoot
Write-Output "Ferramentas portateis verificadas em $toolRoot; PATH global preservado."
