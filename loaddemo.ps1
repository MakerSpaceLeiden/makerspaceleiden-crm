# Notes:
# - Version argument for Python is not used: running separate versions of Python on Windows is quite a hassle
# - MS visual c++ 14 is required for mySql
# - On a 64-bit system, 64-bit Python is required for installation of MySql and Django-dynamic-filenames

# Bash set -e equivalent for powershell, which doesn't respond directly to python/pip error codes
function RunWithErrorCheck ([string]$command) 
{
    iex $command 

    if($lastexitcode -ne 0)
    {
        write-Warning "Script terminated due to an error"
        exit
    }
}

write-host "Loading demo for Makerspace CRM/CMS"

RunWithErrorCheck "python -m venv ./venv/bin/activate" #create virtual environment for crm
RunWithErrorCheck "pip install -r requirements.txt" 

if(Test-Path .\db.sqlite3) #rebuild db using migrations
{
    Remove-Item -Force db.sqlite3
}

RunWithErrorCheck "python manage.py makemigrations"
RunWithErrorCheck "python manage.py migrate"

write-host "Importing Data"
if(Test-Path .\demo\example.json)
{
    RunWithErrorCheck "manage.py loaddata demo/example.json"
}
else
{
    RunWithErrorCheck "python manage.py import-wifi demo/wifi.csv"
    RunWithErrorCheck "python manage.py import-machines demo/mac.csv "
    RunWithErrorCheck "python manage.py import-consolidated demo/consolidated.txt"
    
    $I = read-host "Reset all passwords and generate invites? (Y/N Default: N)"
    if($I -eq "Y")
    {
        RunWithErrorCheck "python manage.py sent-invite --reset --all #typo: send-invite"
    }
    else
    {
        write-host "No invites with password-set requests sent. Passwords are all hardcoded to 1234 for:"
        get-content .\demo\consolidated.txt
    }
}

RunWithErrorCheck "python manage.py runserver"