# Builds the controlled corpus (.docm/.xlsm) via Word/Excel COM automation.
# Reads manifest.json + sources/ produced by oblivionx.corpus.generate and
# writes samples + build_report.json. Word/Excel-authored files guarantee
# valid, executable VBA projects.
#
# NOTE: do NOT use Join-Path for Office target paths — PowerShell 5.1 under
# WSL interop produces strings that make Word's SaveAs2 hang (VBE opens
# invisibly). Use plain string concatenation (verified).
param(
    [Parameter(Mandatory=$true)][string]$ManifestPath,
    [Parameter(Mandatory=$true)][string]$OutDir
)
$ErrorActionPreference = "Continue"
$srcDir = (Split-Path $ManifestPath) + "\sources"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$report = @()

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.AutomationSecurity = 1
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

$idx = 0
foreach ($s in $manifest.samples) {
    $idx++
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $doc = $null
    try {
        $outFile = $OutDir + "\" + $s.id + "." + $s.format
        if ($s.host -eq "word") {
            $doc = $word.Documents.Add()
            $doc.Content.Text = "Oblivion-X corpus sample " + $s.id
        } else {
            $doc = $excel.Workbooks.Add()
            $doc.Worksheets.Item(1).Cells.Item(1,1) = "Oblivion-X corpus sample " + $s.id
        }
        # document module (clear default content first)
        $dm = $doc.VBProject.VBComponents.Item($s.doc_module)
        if ($dm.CodeModule.CountOfLines -gt 0) {
            $dm.CodeModule.DeleteLines(1, $dm.CodeModule.CountOfLines)
        }
        $docSrc = Get-Content ($srcDir + "\" + $s.doc_source) -Raw
        # strip Attribute lines: Word generates them itself, and duplicate
        # Attribute VB_Name lines break the project
        $docSrc = ($docSrc -split "`r`n" | Where-Object { $_ -notmatch "^Attribute" }) -join "`r`n"
        $dm.CodeModule.AddFromString($docSrc)
        # helper procedural module
        $mod = $doc.VBProject.VBComponents.Add(1)  # vbext_ct_StdModule
        $mod.Name = "NewMacros"
        $helpSrc = Get-Content ($srcDir + "\" + $s.helper_source) -Raw
        $helpSrc = ($helpSrc -split "`r`n" | Where-Object { $_ -notmatch "^Attribute" }) -join "`r`n"
        $mod.CodeModule.AddFromString($helpSrc)
        # save
        if ($s.host -eq "word") {
            $doc.SaveAs2($outFile, 13)   # wdFormatXMLDocumentMacroEnabled
        } else {
            $doc.SaveAs($outFile, 52)    # xlOpenXMLWorkbookMacroEnabled
        }
        $doc.Close(0)
        $report += [pscustomobject]@{ id=$s.id; status="ok";
                                      time_ms=$sw.ElapsedMilliseconds; error="" }
    } catch {
        $report += [pscustomobject]@{ id=$s.id; status="error";
                                      time_ms=$sw.ElapsedMilliseconds;
                                      error=$_.Exception.Message }
        if ($doc) { try { $doc.Close(0) } catch {} }
    }
    if (($idx % 20) -eq 0) {
        Write-Output ("progress {0}/{1}" -f $idx, $manifest.samples.Count)
    }
}

$report | ConvertTo-Json | Set-Content ($OutDir + "\build_report.json")
Write-Output ("DONE: {0} samples -> {1}" -f $manifest.samples.Count, $OutDir)
$word.Quit()
$excel.Quit()
