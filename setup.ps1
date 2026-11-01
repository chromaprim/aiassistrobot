param([switch]$NoPull)
if ($NoPull) {
    & "$PSScriptRoot\manage.ps1" setup --no-pull
} else {
    & "$PSScriptRoot\manage.ps1" setup
}
exit $LASTEXITCODE
