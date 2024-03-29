# Automatic build script for standalone applications, using auto-py-to-exe

# Check if auto-py-to-exe is installed
$installedPackages = pip freeze
if ($installedPackages -like "*auto-py-to-exe*") {
    Write-Host "auto-py-to-exe is installed"
} else {
    Write-Host "auto-py-to-exe is not installed, installing now"
    pip install auto-py-to-exe
}

# Get the current location in absolute path
$currentDirectory = Convert-Path -Path "."
$standaloneBuildScript  = "pyinstaller --noconfirm --onefile --console"
$standaloneBuildScript += " --add-data `"$currentDirectory/scripts;scripts/`""
$standaloneBuildScript += " `"$currentDirectory/main.py`""

Write-Host "Building(standalone): $standaloneBuildScript"
Invoke-Expression -Command $standaloneBuildScript

# Remove the build directory
$pathsToRemove = @(
    "$currentDirectory/build",
    "$currentDirectory/__pycache__",
    "$currentDirectory/main.spec"
)

foreach ($path in $pathsToRemove) {
    if (Test-Path -Path $path) {
        Remove-Item -Path $path -Recurse -Force
        Write-Host "Removed intermediary files: $path"
    }
}

Write-Host "Build completed to $currnetDirectory/dist"