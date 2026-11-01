
$ErrorActionPreference = "Stop"

docker cp key-gen:/root/cs2910/keys/spines_keys ./spines_keys
if ($LASTEXITCODE -ne 0) { exit 1 }

docker cp ./spines_keys linux-dev:/root/cs2910/keys/
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Spines keys transferred successfully."
