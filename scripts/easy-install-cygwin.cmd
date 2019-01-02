cd %HOMEDRIVE%%HOMEPATH%\Downloads
powershell -command "wget http://cygwin.com/setup-x86_64.exe"
setup-x86_64.exe --no-admin -v -g -R %HOMEDRIVE%%HOMEPATH%\Cygwin -l "%HOMEDRIVE%%HOMEPATH%\Cygwin" -C Devel -q -v
