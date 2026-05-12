param(
    [switch]$Staged,
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Paths = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-ReviewFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DisplayPath,
        [Parameter(Mandatory = $true)]
        [string]$LiteralPath
    )

    if (-not (Test-Path -LiteralPath $LiteralPath -PathType Leaf)) {
        [Console]::Error.WriteLine("WARNING: review-dump skipped missing file: $DisplayPath")
        return
    }

    Write-Output "===== $DisplayPath ====="
    $content = [string](Get-Content -LiteralPath $LiteralPath -Raw)
    Write-Output $content
    Write-Output ""
}

function Write-StagedReviewFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DisplayPath
    )

    & git cat-file -e ":$DisplayPath" 2>$null
    if ($LASTEXITCODE -ne 0) {
        [Console]::Error.WriteLine("WARNING: review-dump skipped staged file unavailable in index: $DisplayPath")
        return
    }

    Write-Output "===== $DisplayPath ====="
    & git show ":$DisplayPath"
    if ($LASTEXITCODE -ne 0) {
        [Console]::Error.WriteLine("WARNING: review-dump failed to read staged content: $DisplayPath")
        return
    }
    Write-Output ""
}

try {
    if ($Staged -and $Paths.Count -gt 0) {
        [Console]::Error.WriteLine("ERROR: use either -Staged or an explicit file list, not both.")
        exit 1
    }

    if ($Staged) {
        $stagedPaths = @(& git diff --cached --name-only)
        if ($LASTEXITCODE -ne 0) {
            [Console]::Error.WriteLine("ERROR: failed to read staged files from git.")
            exit 1
        }
        if ($stagedPaths.Count -eq 0) {
            [Console]::Error.WriteLine("No staged files found; no review payload produced.")
            exit 0
        }
        foreach ($path in $stagedPaths) {
            Write-StagedReviewFile -DisplayPath $path
        }
        exit 0
    }

    if ($Paths.Count -eq 0) {
        [Console]::Error.WriteLine("ERROR: provide one or more file paths, or use -Staged.")
        exit 1
    }

    foreach ($path in $Paths) {
        Write-ReviewFile -DisplayPath $path -LiteralPath $path
    }
    exit 0
}
catch {
    [Console]::Error.WriteLine("ERROR: review-dump failed: $($_.Exception.Message)")
    exit 1
}
