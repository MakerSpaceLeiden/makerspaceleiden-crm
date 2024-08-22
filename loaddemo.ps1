# Notes:
# - Version argument for Python is not used: running separate versions of Python on Windows is quite a hassle
# - MS visual c++ 14 is required for mySql
# - On a 64-bit system, 64-bit Python is required for installation of MySql and Django-dynamic-filenames

# Bash set -e equivalent for powershell, which doesn't respond directly to python/pip error codes
function RunWithErrorCheck ([string]$command)
{
    Invoke-Expression $command

    if($lastexitcode -ne 0)
    {
        Write-Warning "Script terminated due to an error"
        exit
    }
}

Write-Host "Loading demo for Makerspace CRM/CMS"

RunWithErrorCheck "python -m venv ./venv/bin/activate" #create virtual environment for crm
RunWithErrorCheck ".\venv\bin\activate\Scripts\Activate.ps1"
RunWithErrorCheck "pip install -r requirements.txt"

if(Test-Path .\db.sqlite3) #rebuild db using migrations
{
    Remove-Item -Force db.sqlite3
}

RunWithErrorCheck "python manage.py makemigrations"
RunWithErrorCheck "python manage.py migrate"

Write-Host "Importing Data"
if(Test-Path .\demo\example.json)
{
    RunWithErrorCheck "manage.py loaddata demo/example.json"
}
else
{
    RunWithErrorCheck "python manage.py import-wifi demo/wifi.csv"
    RunWithErrorCheck "python manage.py import-machines demo/mac.csv "
    RunWithErrorCheck "python manage.py import-consolidated demo/consolidated.txt"
    RunWithErrorCheck "python manage.py pettycash-activate-all-users"

    $I = Read-Host "Reset all passwords and generate invites? (Y/N Default: N)"
    if($I -eq "Y")
    {
        RunWithErrorCheck "python manage.py sent-invite --reset --all #typo: send-invite"
    }
    else
    {
        Write-Host "No invites with password-set requests sent. Passwords are all hardcoded to 1234 for:"
        Get-Content .\demo\consolidated.txt | Select-String -Pattern "@"
    }
}

RunWithErrorCheck "python manage.py runserver"
