Param(
    [ValidateSet("makemessages", "compilemessages", "all")]
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

switch ($Command) {
    "makemessages" { Run-Makemessages -LangCode $Lang }
    "compilemessages" { Run-Compilemessages }
    "all" {
        Run-Makemessages -LangCode $Lang
        Run-Compilemessages
    }
}

Write-Host "Done." -ForegroundColor Cyan

