# Установка PYTHONPATH и запуск сервера
$env:PYTHONPATH = (Get-Item -Path ".\").FullName
python .\server\server.py