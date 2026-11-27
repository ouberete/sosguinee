Param(
    [ValidateSet("makemessages", "translate", "compilemessages", "all")]
    [string]$Command = "all",
    [string]$Lang = "en"
)

Write-Host "Using Docker Compose for Django i18n ($Command, lang=$Lang)..." -ForegroundColor Cyan

function Run-Makemessages {
    param([string]$LangCode)
    Write-Host "Running makemessages for '$LangCode'..." -ForegroundColor Green
    docker compose run --rm web python manage.py makemessages -l $LangCode
}

function Run-Compilemessages {
    Write-Host "Compiling messages..." -ForegroundColor Green
    docker compose run --rm web python manage.py compilemessages
}

function Run-Translate {
    param([string]$LangCode)

    if (-not $env:DEEPL_AUTH_KEY) {
        $dotenvPath = Join-Path $PSScriptRoot ".env"
        if (Test-Path $dotenvPath) {
            foreach ($line in Get-Content $dotenvPath) {
                if ($line -match '^\s*DEEPL_AUTH_KEY\s*=\s*(.*?)\s*$') {
                    $env:DEEPL_AUTH_KEY = $Matches[1].Trim('"').Trim("'")
                    break
                }
            }
        }
    }

    if (-not $env:DEEPL_AUTH_KEY) {
        throw "Ajoutez DEEPL_AUTH_KEY dans .env ou dans l'environnement PowerShell."
    }

    Write-Host "Translating empty '$LangCode' messages with DeepL..." -ForegroundColor Green
    docker compose run --rm -e DEEPL_AUTH_KEY web python manage.py translate_messages -l $LangCode
}

switch ($Command) {
    "makemessages" { Run-Makemessages -LangCode $Lang }
    "translate" { Run-Translate -LangCode $Lang }
    "compilemessages" { Run-Compilemessages }
    "all" {
        Run-Makemessages -LangCode $Lang
        Run-Translate -LangCode $Lang
        Run-Compilemessages
    }
}

Write-Host "Done." -ForegroundColor Cyan

