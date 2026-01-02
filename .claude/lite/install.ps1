# Install Claude Code Toolkit Lite globally
# Run: .\install.ps1

$targetDir = "$env:USERPROFILE\.claude\commands"

Write-Host "Installing Claude Code Toolkit Lite..." -ForegroundColor Cyan

# Create directory if needed
if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Write-Host "Created: $targetDir" -ForegroundColor Green
}

# Copy command files (not README)
$commands = @("status.md", "continue.md", "autonomous.md", "review.md", "handoff.md")
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

foreach ($cmd in $commands) {
    $source = Join-Path $scriptDir $cmd
    if (Test-Path $source) {
        Copy-Item $source $targetDir -Force
        Write-Host "Installed: $cmd" -ForegroundColor Green
    }
}

Write-Host "`nDone! Commands available globally:" -ForegroundColor Cyan
Write-Host "  /status    - Check project state"
Write-Host "  /continue  - Resume work"
Write-Host "  /autonomous - Work without interruption"
Write-Host "  /review    - Quick code review"
Write-Host "  /handoff   - End session cleanly"
Write-Host "`nRun 'claude' from any directory to use." -ForegroundColor Yellow
