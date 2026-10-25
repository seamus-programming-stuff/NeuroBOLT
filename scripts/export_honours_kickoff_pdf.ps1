param(
    [string]$PresentationPath = (Join-Path $PSScriptRoot '..\output\presentations\Monash_EEG_honours_kickoff_v2.pptx'),
    [string]$PdfPath = (Join-Path $PSScriptRoot '..\output\pdf\Monash_EEG_honours_kickoff_v2.pdf')
)
$ErrorActionPreference = 'Stop'
$resolvedDeck = (Resolve-Path -LiteralPath $PresentationPath).Path
$resolvedPdf = [System.IO.Path]::GetFullPath($PdfPath)
$existingPowerPoint = @(Get-Process -Name POWERPNT -ErrorAction SilentlyContinue)
$powerPointApp = $null
$openedDeck = $null
try {
    $powerPointApp = New-Object -ComObject PowerPoint.Application
    $powerPointApp.DisplayAlerts = 1
    # Open read-only, without a visible document window. Do not save the PPTX.
    $openedDeck = $powerPointApp.Presentations.Open($resolvedDeck, -1, 0, 0)
    # ppSaveAsPDF = 32; this avoids PowerShell's optional-argument COM binding
    # issue with ExportAsFixedFormat. It writes a separate PDF only.
    $openedDeck.SaveAs($resolvedPdf, 32)
    Write-Output $resolvedPdf
} finally {
    if ($null -ne $openedDeck) {
        $openedDeck.Close()
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($openedDeck)
    }
    if ($null -ne $powerPointApp) {
        if ($existingPowerPoint.Count -eq 0) { $powerPointApp.Quit() }
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($powerPointApp)
    }
}
