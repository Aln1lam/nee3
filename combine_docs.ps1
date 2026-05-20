$files = @()
$ordered = @(".\docs\index.md", ".\docs\overview.md", ".\docs\backend.md", ".\docs\frontend.md", ".\docs\development.md", ".\docs\routes.md")
foreach($f in $ordered){ if (Test-Path $f) { $files += (Resolve-Path $f).Path } }
if (Test-Path .\docs\routes) { $files += Get-ChildItem -Path .\docs\routes -Filter *.md | Sort-Object Name | ForEach-Object { $_.FullName } }
if (Test-Path .\docs\services) { $files += Get-ChildItem -Path .\docs\services -Filter *.md | Sort-Object Name | ForEach-Object { $_.FullName } }
if (Test-Path .\docs\faq.md) { $files += (Resolve-Path .\docs\faq.md).Path }

New-Item -ItemType Directory -Force -Path .\archives | Out-Null

$maxBytes = 15MB
$partIndex = 1
$buffer = "# Combined Documentation`n`nGenerated: $((Get-Date).ToString('o'))`n`n"
$currentBytes = [System.Text.Encoding]::UTF8.GetByteCount($buffer)

foreach($f in $files) {
    try {
        $content = Get-Content $f -Raw -ErrorAction Stop
        $relPath = $f.Replace((Get-Location).Path + "\", "")
        $header = "## Source: $relPath`n`n"
        $block = $header + $content + "`n`n---`n`n"
        $blockBytes = [System.Text.Encoding]::UTF8.GetByteCount($block)

        if ($currentBytes + $blockBytes -gt $maxBytes -and $currentBytes -gt 500) {
            $out = ".\archives\combined_part$partIndex.md"
            $buffer | Out-File -FilePath $out -Encoding utf8
            $partIndex += 1
            $buffer = "# Combined Documentation (continued) `n`nGenerated: $((Get-Date).ToString('o'))`n`n"
            $currentBytes = [System.Text.Encoding]::UTF8.GetByteCount($buffer)
        }

        $buffer += $block
        $currentBytes += $blockBytes
    } catch {
        Write-Warning "Could not read $f"
    }
}

if ($buffer.Length -gt 100) {
    $out = ".\archives\combined_part$partIndex.md"
    $buffer | Out-File -FilePath $out -Encoding utf8
}

Get-ChildItem -Path .\archives\combined_part*.md | Select-Object Name, @{Name='SizeMB';Expression={[math]::Round($_.Length/1MB,2)}} | ConvertTo-Json -Compress
