param([Parameter(Mandatory = $true)][string]$SourceRoot)

$ErrorActionPreference = 'Stop'
if (-not $env:RUNNER_TEMP -or -not $env:GITHUB_ENV) {
    throw 'This helper prepares an ephemeral GitHub Actions build environment.'
}
$sources = Get-Content -LiteralPath (Join-Path $SourceRoot 'native-sources.json') -Raw | ConvertFrom-Json
$vcpkgRoot = Join-Path $env:RUNNER_TEMP 'python-projectm-vcpkg'
if (Test-Path -LiteralPath $vcpkgRoot) {
    throw "Use a fresh runner; $vcpkgRoot already exists."
}
git init $vcpkgRoot
if ($LASTEXITCODE -ne 0) { throw 'vcpkg repository initialization failed.' }
git -C $vcpkgRoot remote add origin https://github.com/microsoft/vcpkg.git
if ($LASTEXITCODE -ne 0) { throw 'vcpkg remote setup failed.' }
git -C $vcpkgRoot fetch --depth 1 origin $sources.vcpkg.commit
if ($LASTEXITCODE -ne 0) { throw 'vcpkg fetch failed.' }
git -C $vcpkgRoot checkout --detach FETCH_HEAD
if ($LASTEXITCODE -ne 0) { throw 'vcpkg checkout failed.' }
& (Join-Path $vcpkgRoot 'bootstrap-vcpkg.bat') -disableMetrics
if ($LASTEXITCODE -ne 0) { throw 'vcpkg bootstrap failed.' }
& (Join-Path $vcpkgRoot 'vcpkg.exe') install `
    "--x-manifest-root=$SourceRoot" `
    "--x-install-root=$vcpkgRoot/installed" `
    "--triplet=$($sources.vcpkg.triplet)"
if ($LASTEXITCODE -ne 0) { throw 'GLEW build failed.' }
$toolchain = (Join-Path $vcpkgRoot 'scripts/buildsystems/vcpkg.cmake').Replace('\', '/')
"VCPKG_ROOT=$vcpkgRoot" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
"CMAKE_TOOLCHAIN_FILE=$toolchain" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
