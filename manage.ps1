param(
    [Parameter(Position=0)]
    [ValidateSet('setup','access','start','stop','restart','status','logs','backup','doctor')]
    [string]$Action = 'status',
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$ExtraArgs
)
$ErrorActionPreference = 'Stop'
$PythonCmd = Get-Command py -ErrorAction SilentlyContinue
$PythonPrefix = @('-3')
if (-not $PythonCmd) {
    $PythonCmd = Get-Command python -ErrorAction SilentlyContinue
    $PythonPrefix = @()
}
if (-not $PythonCmd) {
    Write-Host 'Python 3.9+ is required. Install Python 3.12, then open a NEW terminal.'
    Write-Host 'See docs/INSTALL_WINDOWS.md.'
    exit 1
}
# No redirection or transcript: Python handles private logs and hidden input.
& $PythonCmd.Source @PythonPrefix -X utf8 -u "$PSScriptRoot\manage.py" $Action @ExtraArgs
exit $LASTEXITCODE
