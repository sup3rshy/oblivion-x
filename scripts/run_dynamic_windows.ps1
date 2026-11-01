# Best-effort real dynamic execution of the controlled corpus on Windows.
#
# For every sample this script:
#   1. kills lingering Office processes (COM state is unreliable otherwise)
#   2. opens the file through Word/Excel COM with macros ENABLED
#      (AutomationSecurity = 1 = msoAutomationSecurityLow)
#   3. keeps a MsgBox/InputBox dismisser running in the background
#   4. records open time, close time and any COM error
#   5. writes a VBA-trace log understood by oblivionx.telemetry.normalize
#      (`action<TAB>object<TAB>seconds`) plus a JSON meta file
#
# IMPORTANT LIMITATION: this captures *entry/exit timing and execution
# errors*, not a full API-level trace. Oblivion-style API instrumentation
# (rewriting each call to log itself) is described in the paper and is not
# performed here. Use the simulator for the behavior-level experiments
# (E2-E7); use these traces for real execution timing / failure observation.
#
# Usage:
#   powershell.exe -ExecutionPolicy Bypass -File scripts\run_dynamic_windows.ps1 `
#       -ManifestPath D:\oblivion\outputs\corpus\manifest.json `
#       -SamplesDir  D:\oblivion\outputs\corpus\samples `
#       -OutDir      D:\oblivion\outputs\dynamic_windows `
#       -PerSampleSeconds 8
param(
    [Parameter(Mandatory=$true)][string]$ManifestPath,
    [Parameter(Mandatory=$true)][string]$SamplesDir,
    [Parameter(Mandatory=$true)][string]$OutDir,
    [int]$PerSampleSeconds = 8,
    [int]$Limit = 0
)
$ErrorActionPreference = "Continue"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$samples = $manifest.samples
if ($Limit -gt 0) { $samples = $samples | Select-Object -First $Limit }

$dismisser = Start-Process powershell.exe -PassThru -WindowStyle Hidden `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        (Join-Path $PSScriptRoot "dismiss_activation.ps1"),
        "-Seconds", "$([Math]::Max($PerSampleSeconds * $samples.Count + 120, 600))")

$report = @()
$idx = 0
foreach ($s in $samples) {
    $idx++
    $file = $SamplesDir + "\" + $s.id + "." + $s.format
    $logPath = $OutDir + "\" + $s.id + ".log"
    $metaPath = $OutDir + "\" + $s.id + ".json"
    $lines = @()
    $errorText = $null
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    # clean COM state between samples
    Get-Process WINWORD, EXCEL -ErrorAction SilentlyContinue |
        Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 400

    try {
        if ($s.host -eq "excel") {
            $app = New-Object -ComObject Excel.Application
            $app.Visible = $false
            $app.DisplayAlerts = $false
            $app.AutomationSecurity = 1
            $wb = $app.Workbooks.Open($file)
            $sw.Stop()
            $lines += "macro_entry`tWorkbook_Open`t0.000"
            Start-Sleep -Seconds $PerSampleSeconds
            $wb.Close($false)
            $app.Quit()
            [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wb)
            [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
        } else {
            $app = New-Object -ComObject Word.Application
            $app.Visible = $false
            $app.DisplayAlerts = 0
            $app.AutomationSecurity = 1
            $doc = $app.Documents.Open($file, $false, $true)
            $sw.Stop()
            $lines += "macro_entry`tDocument_Open`t0.000"
            Start-Sleep -Seconds $PerSampleSeconds
            $doc.Close($false)
            $app.Quit()
            [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc)
            [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
        }
    } catch {
        $errorText = $_.Exception.Message
        if ($sw.IsRunning) { $sw.Stop() }
    }

    # 0x800706BA / 0x80010108: the Office process vanished while the macro
    # was running (typically endpoint protection terminating Office after it
    # spawned a suspicious child process). Recorded, never worked around.
    $outcome = "ok"
    if ($errorText) {
        if ($errorText -match "0x800706BA|0x80010108|RPC server") {
            $outcome = "office_terminated"
        } else {
            $outcome = "com_error"
        }
    }

    $elapsed = [Math]::Round($sw.Elapsed.TotalSeconds, 3)
    Set-Content -Path $logPath -Value $lines -Encoding UTF8
    $meta = [ordered]@{
        id             = $s.id
        family         = $s.family
        variant        = $s.variant
        format         = $s.format
        duration_s     = $elapsed
        error          = $errorText
        outcome        = $outcome
        instrumentation = "entry_exit_only"
    }
    $meta | ConvertTo-Json -Compress | Set-Content -Path $metaPath -Encoding UTF8
    $report += $meta

    if ($idx % 10 -eq 0) { Write-Output "progress $idx/$($samples.Count)" }
}

$report | ConvertTo-Json -Depth 4 | Set-Content -Path ($OutDir + "\dynamic_report.json") -Encoding UTF8
Stop-Process -Id $dismisser.Id -Force -ErrorAction SilentlyContinue
Write-Output "DONE: $($samples.Count) samples -> $OutDir"
