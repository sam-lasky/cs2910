
$ErrorActionPreference = "Stop"

docker cp key-gen:/root/cs2910/keys/prime_keys ./prime_keys
if ($LASTEXITCODE -ne 0) { exit 1 }

docker cp ./prime_keys linux-dev:/root/cs2910/keys/
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Prime keys transferred successfully."
