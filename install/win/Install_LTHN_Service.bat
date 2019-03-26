@echo off
:: Obtain elevated command prompt
set "params=%*"
cd /d "%~dp0" && ( if exist "%temp%\getadmin.vbs" del "%temp%\getadmin.vbs" ) && fsutil dirty query %systemdrive% 1>nul 2>nul || (  echo Set UAC = CreateObject^("Shell.Application"^) : UAC.ShellExecute "cmd.exe", "/k cd ""%~sdp0"" && %~s0 %USERPROFILE% %params%", "", "runas", 1 >> "%temp%\getadmin.vbs" && "%temp%\getadmin.vbs" && echo Requesting admin prompt. You may close this window. && exit /B )

:: Check if openvpn is installed
echo Looking for OpenVPN installed bin
echo Original user profile: %1
setlocal ENABLEEXTENSIONS
set KeyName="HKEY_LOCAL_MACHINE\SOFTWARE\OpenVPN"
set ValueName=exe_path
FOR /F "tokens=2*" %%A IN ('REG.exe query "%KeyName%" /v "%ValueName%"') DO (set OpenVpnBin=%%B)
echo %OpenVpnBin%

if not defined OpenVpnBin goto OpenVpnNotInstalled

echo Found OpenVPN bin %OpenVpnBin%
set OpenVpnServerBin=%OpenVpnBin:openvpn.exe=openvpnserv.exe%
echo Using server bin %OpenVpnServerBin%
if "%1"=="" (set ConfigDir=%USERPROFILE%\lthn\var) else (set ConfigDir=%1\lthn\var)
echo Using config dir %ConfigDir%

set SvcName=Lethean
:: Prepare registry keys [required by OpenVPN]
echo Copying registry keys...
set KeyNameNew="HKEY_LOCAL_MACHINE\SOFTWARE\OpenVPN$%SvcName%"
REG.exe COPY "%KeyName%" "%KeyNameNew%"
REG.exe ADD "%KeyNameNew%" /v "config_dir" /t "REG_SZ" /d "%ConfigDir%" /f
echo New registry keys:
REG.exe QUERY "%KeyNameNew%"

:: Create service
echo Creating service "OpenVPNServiceInteractive$%SvcName%"
sc create "OpenVPNServiceInteractive$%SvcName%" ^
   start= auto ^
   binPath= "\"%OpenVpnServerBin%\" -instance \"interactive\" \"$%SvcName%\"" ^
   depend= tap0901/Dhcp ^
   DisplayName= "OpenVPN Interactive Service (%SvcName%)"
:: Start service
sc start "OpenVPNServiceInteractive$%SvcName%"
echo Success! Finished creating and running LTHN service. You may close this window.
exit

:OpenVpnNotInstalled
echo Could not find OpenVPN registry key! Please install OpenVPN first!
pause
exit