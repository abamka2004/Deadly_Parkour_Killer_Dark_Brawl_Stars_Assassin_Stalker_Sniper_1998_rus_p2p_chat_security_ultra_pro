param(
    [Parameter(Mandatory=$true)]
    [string]$yourName,

    [Parameter(Mandatory=$true)]
    [string]$peerName,

    [string]$serverUrl = "http://localhost:8080"
)

python client/client.py $yourName $peerId $serverUrl