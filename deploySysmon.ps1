# Check if Sysmon is already installed on the system via registry key and driver file existence.
# If not, download Sysmon from the official website, extract it, and install it with the default configuration from GitHub.

function Send-WebRequestWithExceptionHandling {
    param (
        [string]$Uri,
        [string]$Path
    )

    try {
        Invoke-WebRequest -Uri $Uri -OutFile $Path
    } catch {
        $StatusCode = $_.Exception.Response.StatusCode.value__
        Write-Error "Failed to download file from $Uri, status code: $StatusCode"
        throw
    }
}

# Check PowerShell version
if ($PSVersionTable.PSVersion -lt [Version]'5.0') {
    Write-Output "Powershell version is less than 5.0, please upgrade to 5.0 or higher"
    exit 1
}

# Check if Sysmon is already installed
$Sysmon64RegistryPath = "HKLM:\SYSTEM\CurrentControlSet\Services\sysmon64"
$Sysmon64DriverPath = "C:\Windows\System32\drivers\sysmon64.sys"

if ($Sysmon64DriverPath -and $Sysmon64RegistryPath) {
    Write-Host "[OK] Sysmon is already installed on the system(registry key and driver file exist)."
    exit 0
}

$DownloadDirectory = (New-Object -ComObject Shell.Application).NameSpace("shell:Downloads").Self.Path
$RandomHexString = -join ((48..57) + (97..102) | Get-Random -Count 8 | ForEach-Object { [char]$_ })
$SysmonZipPath = Join-Path -Path $DownloadDirectory -ChildPath "Sysmon_$RandomHexString.zip"
$SysmonDirPath = Join-Path -Path $DownloadDirectory -ChildPath "Sysmon_$RandomHexString"

Write-Host "[..] Downloading Sysmon to $DownloadDirectory"
Send-WebRequestWithExceptionHandling -Uri "https://download.sysinternals.com/files/Sysmon.zip" -Path $SysmonZipPath

Write-Host "[..] Extracting Sysmon to $SysmonDirPath"
Expand-Archive -Path $SysmonZipPath -DestinationPath $SysmonDirPath -Force

Write-Host "[..] Installing Sysmon Rule set to $SysmonDirPath"
$SysmonDefaultConfigPath = Join-Path -Path $SysmonDirPath -ChildPath "sysmonconfig-export.xml"
Send-WebRequestWithExceptionHandling -Uri "https://raw.githubusercontent.com/olafhartong/sysmon-modular/master/sysmonconfig.xml" -Path $SysmonDefaultConfigPath

Write-Host "[..] Installing Sysmon"
Start-Process -FilePath (Join-Path -Path $SysmonDirPath -ChildPath "sysmon64.exe") -ArgumentList "-accepteula -i $SysmonDefaultConfigPath" -Wait

Write-Host "[OK] Installed Sysmon to $SysmonDirPath completely."
exit 0