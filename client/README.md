# Client specific builds and scripts

## Linux
We use system packages and libraries, you do not need to compile anything.

## Windows
We use cygwin to compile haproxy binaries.
You can use our [easy-install-cygwin.cmd]:(https://raw.githubusercontent.com/valiant1x/intense-vpn/config-sdp/easy-install-cygwin.cmd)
Download it and run. It will install and preconfigure cygwin environment for build.

### haproxy
You can use our [compile script]:(https://github.com/valiant1x/intense-vpn/blob/config-sdp/client/haproxy/easy-build-cygwin.sh) which has to be run inside of cygwin environment 
```
wget https://github.com/valiant1x/intense-vpn/blob/config-sdp/client/haproxy/easy-build-cygwin.sh
sh easy-build-cygwin.sh
```
