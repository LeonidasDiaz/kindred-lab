# Rutina después de cada partida: importar, anotar la última partida, ver el resumen, tus muertes y tus defensivos.
# Uso (desde cualquier carpeta):  .\rutina.ps1
Set-Location $PSScriptRoot
$env:PYTHONPATH = "src"
$registro = "registro/partidas.csv"

function Contar-Partidas {
    if (-not (Test-Path $registro)) { return 0 }
    return @(Import-Csv $registro -Encoding UTF8 | Where-Object { $_.match_id }).Count
}

# 1. Importar
$antes = Contar-Partidas
python -m kindred_lab partidas importar --cantidad 10
if ($LASTEXITCODE -ne 0) {
    Write-Host "La importación falló (¿caducó la clave de Riot?). No se anota nada para no tocar la partida anterior."
    exit 1
}
$nuevas = (Contar-Partidas) - $antes

# 2 y 3. Anotar la última partida (solo si entró una nueva; si no, 'ultima' sería la anterior)
if ($nuevas -lt 1) {
    Write-Host "`nNo hay partidas nuevas: no se anota nada."
} else {
    if ($nuevas -gt 1) {
        Write-Host "`nEntraron $nuevas partidas nuevas; esto anota solo la más reciente."
        Write-Host "Las demás: python -m kindred_lab partidas anotar <match_id> --alcance si|no"
    }
    do {
        $alcance = (Read-Host "`nEn la selección, ¿decidiste que alguien te alcanzaba sin fallar en los primeros 5 minutos? (si/no)").Trim().ToLower() -replace "í", "i"
    } until ($alcance -in @("si", "no"))
    $nota = (Read-Host "Lección de la partida (una sola, Enter para omitir)").Trim()
    if ($nota) {
        python -m kindred_lab partidas anotar ultima --alcance $alcance --nota $nota
    } else {
        python -m kindred_lab partidas anotar ultima --alcance $alcance
    }
}

# 4. Resumen
Write-Host ""
python -m kindred_lab partidas resumen

# 5. Tus muertes de la última partida, una por una
Write-Host ""
python -m kindred_lab jungla --ultima

# 6. Auditoría de tus defensivos en esa partida
Write-Host ""
python -m kindred_lab objetos defensivo --ultima

# 7. Commit del registro (solo ese archivo). Si git falla, se avisa y ya.
try {
    $cambios = git status --porcelain -- $registro
    if ($LASTEXITCODE -ne 0) { throw "git status falló" }
    if ($cambios) {
        $enCommit = @(git show "HEAD:$registro" | ConvertFrom-Csv | ForEach-Object { $_.match_id })
        if ($LASTEXITCODE -ne 0) { throw "git show falló" }
        $partidas = Import-Csv $registro -Encoding UTF8 |
            Where-Object { $_.match_id -and $_.match_id -notin $enCommit } |
            Sort-Object { [long]($_.match_id -replace "\D", "") } -Descending
        if ($partidas) {
            $mensaje = ($partidas | ForEach-Object { "Partida $($_.match_id): $($_.resultado)" }) -join "; "
        } else {
            $mensaje = "Registro: anotaciones"
        }
        git commit --quiet -m $mensaje -- $registro
        if ($LASTEXITCODE -ne 0) { throw "git commit falló" }
        Write-Host "`nCommit: $mensaje"
    }
} catch {
    Write-Host "`nAviso: no se pudo hacer el commit del registro ($_). Hazlo a mano con git."
}
