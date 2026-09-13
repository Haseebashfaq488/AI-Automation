# Sync the Chrome profile into the sidecar (run when the WhatsApp session changes)
# Chrome must be CLOSED before running this script.
$ErrorActionPreference = "Stop"
$src = "$env:LOCALAPPDATA\Google\Chrome\User Data"
$dst = "D:\Ai automation backend\backend\whatsapp_service\chrome_profile_copy"

$chrome = Get-Process -Name "chrome" -ErrorAction SilentlyContinue
if ($chrome) {
    Write-Host "ERROR: Chrome is running. Close Chrome completely, then re-run." -ForegroundColor Red
    exit 1
}

Write-Host "Copying profile (this can take a minute)..."
robocopy "$src" "$dst" /E /XD "$src\Default\Cache" "$src\Default\Code Cache" "$src\Default\GPUCache" "$src\Default\DawnGraphiteCache" "$src\Default\DawnWebGPUCache" "$src\Default\Extensions" "$src\Default\Shared Dictionary" "$src\Default\optimization_guide_hint_cache_store" "$src\Default\JumpListIconsMostVisited" "$src\Default\JumpListIconsRecent" "$src\GrShaderCache" "$src\ShaderCache" "$src\component_updates" /NFL /NDL /NJH /NJS /NC /NS | Out-Null
Write-Host "Done. Restart the whatsapp_service to pick up the fresh profile." -ForegroundColor Green
