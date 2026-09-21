<#
.SYNOPSIS
    Provisions the Azure resources needed to run the InterviewAgent backend against real cloud services.
.DESCRIPTION
    Creates (or reuses) a resource group, then provisions:
      - Azure SQL Database (Basic tier) — app database
      - Azure Cache for Redis (Basic C0) — rate limiting / caching
      - Azure OpenAI resource + gpt-4o-mini deployment — interview question/evaluation agents
      - Azure AI Speech resource — text-to-speech / speech-to-text
    Requires the Azure CLI (az) installed and available on PATH.
.PARAMETER SubscriptionId
    Azure subscription ID/name to use. If omitted, uses the currently active az CLI subscription
    for the signed-in account.
.PARAMETER ResourceGroup
    Resource group name. Defaults to "Learn_RG".
.PARAMETER Location
    Azure region. Defaults to "eastus".
.PARAMETER NamePrefix
    Prefix used to build globally-unique resource names. Defaults to "interviewagent".
.PARAMETER SkipOpenAI
    Skip creating the Azure OpenAI resource (useful if your subscription isn't approved for it yet).
.PARAMETER SkipSpeech
    Skip creating the Azure AI Speech resource.
.EXAMPLE
    ./infra/scripts/create-azure-resources.ps1
.EXAMPLE
    ./infra/scripts/create-azure-resources.ps1 -ResourceGroup Learn_RG -Location eastus2 -SkipSpeech
#>
param(
    [string]$SubscriptionId,
    [string]$ResourceGroup = "Learn_RG",
    [string]$Location = "eastus",
    [string]$SqlLocation = "eastus2",
    [string]$NamePrefix = "interviewagent",
    [switch]$SkipOpenAI,
    [switch]$SkipSpeech
)

$ErrorActionPreference = "Stop"
$expectedAccount = "raazesh066@outlook.com"

function Assert-AzCli {
    if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
        throw "Azure CLI (az) not found. Install it from https://aka.ms/installazurecliwindows and re-run this script."
    }
}

Assert-AzCli

Write-Host "Checking Azure CLI login..." -ForegroundColor Cyan
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Not logged in. Launching 'az login' — sign in with $expectedAccount." -ForegroundColor Yellow
    az login | Out-Null
    $account = az account show | ConvertFrom-Json
}

if ($SubscriptionId) {
    az account set --subscription $SubscriptionId
    $account = az account show | ConvertFrom-Json
}

if ($account.user.name -ne $expectedAccount) {
    Write-Warning "Signed in as '$($account.user.name)', not '$expectedAccount'. Run 'az login' with the correct account, or pass -SubscriptionId, if this is wrong."
}
Write-Host "Using subscription: $($account.name) ($($account.id))" -ForegroundColor Green

# Unique suffix so globally-scoped resource names (SQL Server/Redis/Cognitive Services) don't collide
$suffix = -join ((48..57) + (97..122) | Get-Random -Count 6 | ForEach-Object { [char]$_ })
$sqlServerName = "$NamePrefix-sql-$suffix"
$redisName = "$NamePrefix-redis-$suffix"
$openAiName = "$NamePrefix-openai-$suffix"
$speechName = "$NamePrefix-speech-$suffix"
$sqlDbName = "interview_db"
$sqlAdminUser = "interview_admin"
$sqlAdminPassword = (-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 20 | ForEach-Object { [char]$_ })) + "!1Aa"

Write-Host "`nResource group: $ResourceGroup ($Location)" -ForegroundColor Cyan
az group create --name $ResourceGroup --location $Location --output none

# ---------------------------------------------------------------------------
# 1. Azure SQL Database
# ---------------------------------------------------------------------------
Write-Host "`nCreating Azure SQL logical server '$sqlServerName' in $SqlLocation..." -ForegroundColor Cyan
az sql server create `
    --resource-group $ResourceGroup `
    --name $sqlServerName `
    --location $SqlLocation `
    --admin-user $sqlAdminUser `
    --admin-password $sqlAdminPassword `
    --output none
if ($LASTEXITCODE -ne 0) { throw "sql server create failed with exit code $LASTEXITCODE (try a different -SqlLocation)" }

Write-Host "Allowing your current IP and Azure services through the SQL Server firewall..." -ForegroundColor Cyan
az sql server firewall-rule create `
    --resource-group $ResourceGroup `
    --server $sqlServerName `
    --name AllowAzureServices `
    --start-ip-address 0.0.0.0 `
    --end-ip-address 0.0.0.0 `
    --output none
try {
    $clientIp = (Invoke-RestMethod -Uri "https://api.ipify.org?format=text").Trim()
    az sql server firewall-rule create `
        --resource-group $ResourceGroup `
        --server $sqlServerName `
        --name AllowClientIP `
        --start-ip-address $clientIp `
        --end-ip-address $clientIp `
        --output none
} catch {
    Write-Warning "Could not auto-detect/allow your client IP: $_. Add a firewall rule manually if you need to connect from this machine."
}

Write-Host "Creating database '$sqlDbName' (Basic tier)..." -ForegroundColor Cyan
az sql db create `
    --resource-group $ResourceGroup `
    --server $sqlServerName `
    --name $sqlDbName `
    --edition Basic `
    --output none

$sqlHost = "$sqlServerName.database.windows.net"

# ---------------------------------------------------------------------------
# 2. Azure Cache for Redis
# ---------------------------------------------------------------------------
Write-Host "`nCreating Azure Cache for Redis '$redisName' (Basic C0)..." -ForegroundColor Cyan
az redis create `
    --resource-group $ResourceGroup `
    --name $redisName `
    --location $Location `
    --sku Basic `
    --vm-size C0 `
    --output none
if ($LASTEXITCODE -ne 0) { throw "redis create failed with exit code $LASTEXITCODE" }

Write-Host "Waiting for Redis to finish provisioning (can take several minutes)..." -ForegroundColor Yellow
do {
    Start-Sleep -Seconds 20
    $state = az redis show --resource-group $ResourceGroup --name $redisName --query provisioningState -o tsv
    Write-Host "  Redis provisioning state: $state" -ForegroundColor Yellow
} while ($state -eq "Creating")

$redisKey = az redis list-keys --resource-group $ResourceGroup --name $redisName --query primaryKey -o tsv
$redisUrl = "rediss://:$($redisKey)@$($redisName).redis.cache.windows.net:6380/0"

# ---------------------------------------------------------------------------
# 3. Azure OpenAI
# ---------------------------------------------------------------------------
$openAiEndpoint = ""
$openAiKey = ""
$openAiDeployment = "gpt-4o-mini"
if (-not $SkipOpenAI) {
    try {
        Write-Host "`nCreating Azure OpenAI resource '$openAiName'..." -ForegroundColor Cyan
        az cognitiveservices account create `
            --resource-group $ResourceGroup `
            --name $openAiName `
            --location $Location `
            --kind OpenAI `
            --sku S0 `
            --custom-domain $openAiName `
            --yes `
            --output none

        Write-Host "Deploying model '$openAiDeployment'..." -ForegroundColor Cyan
        az cognitiveservices account deployment create `
            --resource-group $ResourceGroup `
            --name $openAiName `
            --deployment-name $openAiDeployment `
            --model-name gpt-4o-mini `
            --model-version "2024-07-18" `
            --model-format OpenAI `
            --sku-name GlobalStandard `
            --sku-capacity 10 `
            --output none
        if ($LASTEXITCODE -ne 0) { throw "deployment create failed with exit code $LASTEXITCODE" }

        $openAiEndpoint = az cognitiveservices account show --resource-group $ResourceGroup --name $openAiName --query properties.endpoint -o tsv
        $openAiKey = az cognitiveservices account keys list --resource-group $ResourceGroup --name $openAiName --query key1 -o tsv
    } catch {
        Write-Warning "Azure OpenAI provisioning failed (subscription may not be approved for Azure OpenAI access): $_"
        Write-Warning "Re-run with -SkipOpenAI, or request access at https://aka.ms/oai/access, then fill AZURE_OPENAI_* into backend/.env manually."
    }
} else {
    Write-Host "`nSkipping Azure OpenAI (per -SkipOpenAI)." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# 4. Azure AI Speech
# ---------------------------------------------------------------------------
$speechKey = ""
if (-not $SkipSpeech) {
    try {
        Write-Host "`nCreating Azure AI Speech resource '$speechName'..." -ForegroundColor Cyan
        az cognitiveservices account create `
            --resource-group $ResourceGroup `
            --name $speechName `
            --location $Location `
            --kind SpeechServices `
            --sku S0 `
            --yes `
            --output none

        $speechKey = az cognitiveservices account keys list --resource-group $ResourceGroup --name $speechName --query key1 -o tsv
    } catch {
        Write-Warning "Azure AI Speech provisioning failed: $_"
    }
} else {
    Write-Host "`nSkipping Azure AI Speech (per -SkipSpeech)." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# Write generated env values for local backend use (gitignored — contains secrets)
# ---------------------------------------------------------------------------
$envPath = Join-Path $PSScriptRoot "..\..\backend\.env.azure"
@"
# Generated by create-azure-resources.ps1 on $(Get-Date -Format o)
# Merge these values into backend/.env — DO NOT COMMIT THIS FILE (already covered by .gitignore).
DATABASE_SERVER=$sqlHost
DATABASE_NAME=$sqlDbName
DATABASE_USER=$sqlAdminUser
DATABASE_PASSWORD=$sqlAdminPassword
DATABASE_DRIVER=ODBC Driver 18 for SQL Server
DATABASE_ENCRYPT=true
DATABASE_TRUST_SERVER_CERTIFICATE=false
REDIS_URL=$redisUrl
AZURE_OPENAI_ENDPOINT=$openAiEndpoint
AZURE_OPENAI_API_KEY=$openAiKey
AZURE_OPENAI_DEPLOYMENT_GPT4O=$openAiDeployment
AZURE_SPEECH_KEY=$speechKey
AZURE_SPEECH_REGION=$Location
"@ | Set-Content -Path $envPath -Encoding utf8

Write-Host "`nDone. Resource group: $ResourceGroup" -ForegroundColor Green
Write-Host "Generated env values written to: $envPath" -ForegroundColor Green
Write-Host "Merge them into backend/.env, then follow docs/START_APPLICATION.md to run the app." -ForegroundColor Green
Write-Host "`nSQL admin user:     $sqlAdminUser" -ForegroundColor Magenta
Write-Host "SQL admin password: $sqlAdminPassword  (save this securely — shown only once)" -ForegroundColor Magenta
