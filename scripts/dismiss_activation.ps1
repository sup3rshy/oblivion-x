# Dismisses the "Microsoft Office Activation Wizard" dialog that pops up on
# unactivated Office installs and blocks Word/Excel COM automation.
# Run this in parallel with any long Office automation job.
param(
    [int]$Seconds = 3600,
    [string[]]$ProcessNames = @("WINWORD", "EXCEL")
)
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Dismisser {
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr lParam);
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll")] public static extern int GetClassName(IntPtr hWnd, System.Text.StringBuilder sb, int max);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder sb, int max);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
}
"@
$end = (Get-Date).AddSeconds($Seconds)
$dismissed = 0
while ((Get-Date) -lt $end) {
    foreach ($pn in $ProcessNames) {
        $procs = Get-Process -Name $pn -ErrorAction SilentlyContinue
        foreach ($p in $procs) {
            $pidv = $p.Id
            [Dismisser]::EnumWindows({
                param($h, $l)
                $wp = [uint32]0
                [Dismisser]::GetWindowThreadProcessId($h, [ref]$wp) | Out-Null
                if ($wp -eq $pidv) {
                    $cb = New-Object System.Text.StringBuilder 256
                    [Dismisser]::GetClassName($h, $cb, 256) | Out-Null
                    if ($cb.ToString() -eq "NUIDialog") {
                        $sb = New-Object System.Text.StringBuilder 256
                        [Dismisser]::GetWindowText($h, $sb, 256) | Out-Null
                        if ($sb.ToString() -match "Activation|License|Sign in|Office") {
                            [Dismisser]::PostMessage($h, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null
                            $dismissed++
                        }
                    }
                }
                return $true
            }, [IntPtr]::Zero) | Out-Null
        }
    }
    Start-Sleep -Seconds 2
}
Write-Output ("dismisser finished, dialogs dismissed: " + $dismissed)
