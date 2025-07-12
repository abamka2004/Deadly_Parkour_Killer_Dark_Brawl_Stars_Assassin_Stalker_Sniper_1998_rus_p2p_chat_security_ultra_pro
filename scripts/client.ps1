param(
    [Parameter(Mandatory=$true)]
    [string]$yourName,

    [Parameter(Mandatory=$true)]
    [string]$peerName,

    [Parameter(Mandatory=$true)]
    [string]$serverUrl
)

# Установка PYTHONPATH и запуск клиента
$env:PYTHONPATH = (Get-Item -Path ".\").FullName
python .\client\client.py $yourName $peerName $serverUrl