# ═══════════════════════════════════════════════════════════
#  Pomodoro Timer Launcher - Always-on-Top Window
# ═══════════════════════════════════════════════════════════
# Launches pomodoro.html in an always-on-top window.
# Requires Microsoft Edge (default on Windows 10/11).
# ═══════════════════════════════════════════════════════════

param(
    [switch]$NoTopMost  # Skip setting always-on-top
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$htmlPath = Join-Path $scriptDir "pomodoro.html"

if (-not (Test-Path $htmlPath)) {
    Write-Host "ERROR: Cannot find pomodoro.html at $htmlPath" -ForegroundColor Red
    exit 1
}

$url = "file:///" + ($htmlPath -replace '\\', '/')

# Try Microsoft Edge app mode first (no toolbar, clean window)
$edge = Get-Command msedge.exe -ErrorAction SilentlyContinue

if ($edge) {
    Write-Host "Launching with Microsoft Edge (app mode)..." -ForegroundColor Cyan
    Start-Process msedge.exe -ArgumentList @(
        "--app=$url",
        "--new-window",
        "--window-size=460,700",
        "--disable-extensions"
    )
} else {
    # Fallback: try Chrome app mode
    $chrome = Get-Command chrome.exe -ErrorAction SilentlyContinue
    if ($chrome) {
        Write-Host "Launching with Google Chrome (app mode)..." -ForegroundColor Cyan
        Start-Process chrome.exe -ArgumentList @(
            "--app=$url",
            "--new-window",
            "--window-size=460,700"
        )
    } else {
        # Last resort: open in default browser
        Write-Host "Launching with default browser..." -ForegroundColor Yellow
        Write-Host "(Install Edge or Chrome for always-on-top support)" -ForegroundColor Yellow
        Start-Process $url
        exit 0
    }
}

if (-not $NoTopMost) {
    # Wait for the window to appear and set it topmost
    Write-Host "Waiting for window..." -ForegroundColor Cyan
    Start-Sleep -Seconds 1.5

    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class Win32Window {
    [DllImport("user32.dll")]
    public static extern IntPtr FindWindowEx(IntPtr parent, IntPtr childAfter, string className, string windowName);
    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    public static IntPtr HWND_TOPMOST = new IntPtr(-1);
    public const uint SWP_NOMOVE = 0x0002;
    public const uint SWP_NOSIZE = 0x0001;
    public const uint SWP_SHOWWINDOW = 0x0040;

    public static IntPtr FindWindowByTitle(string title) {
        IntPtr hWnd = IntPtr.Zero;
        StringBuilder sb = new StringBuilder(256);
        while (true) {
            hWnd = FindWindowEx(IntPtr.Zero, hWnd, null, null);
            if (hWnd == IntPtr.Zero) break;
            GetWindowText(hWnd, sb, sb.Capacity);
            if (sb.ToString().Contains(title)) return hWnd;
        }
        return IntPtr.Zero;
    }

    public static void SetTopMost(IntPtr hWnd) {
        if (hWnd != IntPtr.Zero)
            SetWindowPos(hWnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW);
    }
}
"@

    # Try to find the pomodoro window by title
    $hwnd = [Win32Window]::FindWindowByTitle("Pomodoro")
    if ($hwnd -ne [IntPtr]::Zero) {
        [Win32Window]::SetTopMost($hwnd)
        Write-Host "OK - Window set to always-on-top" -ForegroundColor Green
    } else {
        Write-Host "WARN - Could not find window to set topmost" -ForegroundColor Yellow
        Write-Host "  Tip: Use PowerToys Win+Ctrl+T to pin any window on top" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Pomodoro Timer started!" -ForegroundColor Green
Write-Host "  Shortcuts: Space=Start/Pause  R=Reset  S=Skip  1/2/3=Tabs" -ForegroundColor Gray
