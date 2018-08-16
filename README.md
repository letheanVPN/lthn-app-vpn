# intense-vpn
This repository contains code needed to setup and run Intense Coin Virtual Private Network (VPN).

## Design
ITNS VPN dispatcher is tool which make all orchestration of other packages. It does not provide any VPN functionality by itself.
It uses system packages whenever it is possible but it runs all instances manually after invoking.

### sudo
By default, all scripts have lowest permissions as possible. We do not recommend to run anything as root. It is better to configure sudo access for
your user and use it. Just install sudo and configure VPN user to run all sudo commands without password.
sudoers file snippet:
```
vpnuser  ALL=(ALL:ALL) NOPASSWD:ALL
```

### Proxy mode (mandatory)
In proxy mode, it runs preconfigured haproxy which acts as frontend for clients (authenticated by ITNS payments) and use other HTTP proxy as backend.
Easiest way is to use with squid but it can be any kind of HTTP proxy.

### VPN mode
If you decide to run ITNS VPN dispatcher in VPN mode, it starts OpenVpn server authenticated by ITNS payments. 

### Session management
Dispatcher orchestrates all proxy and VPN instances and take care of authentication and session creation. 
In huge sites, this could generate big load. Session management can be turned off. In such cases, sessions which are alive after payment is spent,
will not be terminated automatically.

## Requirements
 * python3
 * python3-pip
 * haproxy
 * squid or other HTTP proxy
 * openvpn (optional)
 * sudo installed and configured

There are more required python classes but they will be installed
automatically during install.

On debian, use standard packager:
```bash
apt-get install python3 python3-pip haproxy sudo

```

## Configure and install
Project is configured by standard configure script. You can change basic parameters of service via this script.
It will ask you for all parameters and generate sdp.json and dispatcher.ini. 
Please note that config files will be generic and it is good to review and
edit them before real usage. You can run configure script more times if
you want to change parameters but you have to do *make clean* first.
If you use *FORCE=1* during make install, it will overwrite your configs.
Without this flag, all configs and keys are left untouched.

### Wallet
Dispatcher needs to have wallet configured before run and it needs to have
wallet-vpn-rpc binary runing. Please note that there are two passwords. One
for unlocking wallet and one for dispatcher RPC calls.
You can download these binary from [here](https://itns.s3.us-east-2.amazonaws.com/Cli/Cli_Ubuntu160464bitStaticRelease/385/intensecoin-cli-linux-64bit-HEAD-44a4437.tar.bz2) (you need master intensecoin branch)
```bash
intense-wallet-vpn-rpc --vpn-rpc-bind-port 13660 --wallet-file itnsvpn --rpc-login
dispatcher:<somepassword> --password <walletpassword>

```

### Basic install
See ./configure.sh --help for more fine-tuned options
```bash
pip3 install -r requirements.txt
./configure.sh --easy [--with-wallet wallet_address]
make install [FORCE=1]
```

### Public configuration - sdp.json
*/opt/itns/etc/sdp.json* describes local services for orchestration. It is uploaded to SDP server by --upload-sdp option. Note that uploading to SDP server is paid service. 
After installation, you must generate SDP which is required to run.
You can either answer question during wizard or you can use cmdline option to set defaults. See help.
```bash
/opt/itns/bin/itnsdispatcher --generate-sdp --wallet-address some_wallet_address [--sdp-service-name someName] ...

```

### Private configuration - dispatcher.ini
*/opt/itns/etc/dispatcher.ini* contains local information needed to run dispatcher. It is local file containing private information. Do not upload it to any place.
By default, *make install* will generate default file for you but you need to configure it to respect your needs.
File format:
```ini
[global]
;debug=DEBUG
ca={ca}
;provider-type=commercial
provider-id={providerid}
provider-key={providerkey}
provider-name=Provider
provider-terms=Some Terms
;provider-terms=@from_file.txt

;;; Wallet
;wallet-address={wallet_address}
;wallet-rpc-url=http://127.0.0.1:13660/json_rpc
;wallet-username={wuser}
;wallet-password={wpasword}

;;; SDP
;sdp-servers={sdpservers}

; Service specific options. Each section [service-id] contains settings for service with given id (need to correspond with SDP)
[service-1A]
name=Proxy
backend_proxy_server=localhost:3128
crt={hacrt}
key={hakey}
crtkey={haboth}

[service-1B]
crt={vpncrt}
key={vpnkey}
crtkey={vpnboth}
reneg=60

```

### Automated install
For fully automated install, please use our easy deploy script. Please note that this script works only if system is clean and sudo is already configured for user which runs this.
Never run this on configured system! It will overwrite config files!
```bash
wget https://raw.githubusercontent.com/valiant1x/intense-vpn/master/server/easy-deploy-node.sh
chmod +x easy-deploy-node.sh
BRANCH=master ./easy-deploy-node.sh

```

You can use more env variables to tune parameters. See script header for available env variables:
```bash
[ -z "$BRANCH" ] && BRANCH=master
[ -z "$CAPASS" ] && CAPASS=1234
[ -z "$CACN" ] && CACN=ITNSFakeNode
[ -z "$ENDPOINT" ] && ENDPOINT="1.2.3.4"
[ -z "$PORT" ] && PORT="8080"
[ -z "$PROVTYPE" ] && PROVTYPE="residental"
[ -z "$WALLET" ] && WALLET="izxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
[ -z "$EMAIL" ] && EMAIL=""

```

## Usage 
```bash
 /opt/itns/bin/itnsdispatcher -h
usage: itnsdispatcher [-f CONFIGFILE] [-h] [-s SDPFILE] [-l LEVEL] [-A FILE]
                      [-a FILE] [--refresh-time SEC] [--save-time SEC]
                      [-lc FILE] [-v] [-G PREFIX] [-S] [-C SERVICEID] [-D]
                      [-U] [--sdp-service-crt FILE] [--sdp-service-type TYPE]
                      [--sdp-service-fqdn FQDN] [--sdp-service-port NUMBER]
                      [--sdp-service-name NAME] [--sdp-service-id NUMBER]
                      [--sdp-service-cost ITNS] [--sdp-service-disable NUMBER]
                      [--sdp-service-refunds NUMBER]
                      [--sdp-service-dlspeed Mbps]
                      [--sdp-service-ulspeed Mbps]
                      [--sdp-service-prepaid-mins TIME]
                      [--sdp-service-verifications NUMBER] --ca ca.crt
                      [--wallet-rpc-uri URI] [--wallet-username USER]
                      [--wallet-password PW] [--sdp-uri URL [URL ...]]
                      --provider-id PROVIDERID --provider-key PROVIDERKEY
                      --provider-name NAME [--provider-type TYPE]
                      [--provider-terms TEXT]

Args that start with '--' (eg. -h) can also be set in a config file (specified
via -f). Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for
details, see syntax at https://goo.gl/R74nmi). If an arg is specified in more
than one place, then commandline values override config file values which
override defaults.

optional arguments:
  -f CONFIGFILE, --config CONFIGFILE
                        Config file (default: /opt/itns//etc/dispatcher.ini)
  -h, --help            Help (default: None)
  -s SDPFILE, --sdp SDPFILE
                        SDP file (default: /opt/itns//etc/sdp.json)
  -l LEVEL, --log-level LEVEL
                        Log level (default: WARNING)
  -A FILE, --authids FILE
                        Authids db file. Use "none" to disable. (default:
                        /opt/itns//var/authids.db)
  -a FILE, --audit-log FILE
                        Audit log file (default: /opt/itns//var/log/audit.log)
  --refresh-time SEC    Refresh frequency. Set to 0 for disable autorefresh.
                        (default: 30)
  --save-time SEC       Save authid frequency. Use 0 to not save authid
                        regularly. (default: 10)
  -lc FILE, --logging-conf FILE
                        Logging config file (default: None)
  -v, --verbose         Be more verbose on output (default: None)
  -G PREFIX, --generate-providerid PREFIX
                        Generate providerid files (default: None)
  -S, --generate-server-configs
                        Generate configs for services and exit (default: None)
  -C SERVICEID, --generate-client-config SERVICEID
                        Generate client config for specified service on stdout
                        and exit (default: None)
  -D, --generate-sdp    Generate SDP by wizzard (default: None)
  -U, --upload-sdp      Upload SDP (default: None)
  --sdp-service-crt FILE
                        Provider Proxy crt (for SDP edit/creation only)
                        (default: None)
  --sdp-service-type TYPE
                        Service type (proxy or vpn) (default: None)
  --sdp-service-fqdn FQDN
                        Service FQDN or IP (for SDP service edit/creation
                        only) (default: None)
  --sdp-service-port NUMBER
                        Service port (for SDP service edit/creation only)
                        (default: None)
  --sdp-service-name NAME
                        Service name (for SDP service edit/creation only)
                        (default: None)
  --sdp-service-id NUMBER
                        Service ID (for SDP service edit/creation only)
                        (default: None)
  --sdp-service-cost ITNS
                        Service cost (for SDP service edit/creation only)
                        (default: None)
  --sdp-service-disable NUMBER
                        Set to true to disable service; otherwise leave false.
                        (default: False)
  --sdp-service-refunds NUMBER
                        Allow refunds for Service (for SDP service
                        edit/creation only) (default: False)
  --sdp-service-dlspeed Mbps
                        Download speed for Service (for SDP service
                        edit/creation only) (default: None)
  --sdp-service-ulspeed Mbps
                        Upload speed for Service (for SDP service
                        edit/creation only) (default: None)
  --sdp-service-prepaid-mins TIME
                        Prepaid minutes for Service (for SDP service
                        edit/creation only) (default: None)
  --sdp-service-verifications NUMBER
                        Verifications needed for Service (for SDP service
                        edit/creation only) (default: None)
  --ca ca.crt           Set certificate authority file (default: None)
  --wallet-rpc-uri URI  Wallet URI (default: http://127.0.0.1:13660/json_rpc)
  --wallet-username USER
                        Wallet username (default: dispatcher)
  --wallet-password PW  Wallet passwd (default: None)
  --sdp-uri URL [URL ...]
                        SDP server(s) (default: https://jhx4eq5ijc.execute-
                        api.us-east-1.amazonaws.com/dev/v1)
  --provider-id PROVIDERID
                        ProviderID (public ed25519 key) (default: None)
  --provider-key PROVIDERKEY
                        ProviderID (private ed25519 key) (default: None)
  --provider-name NAME  Provider Name (default: None)
  --provider-type TYPE  Provider type (default: residential)
  --provider-terms TEXT
                        Provider terms (default: None)

Use -v option to more help info.
Happy flying with better privacy!

```

## Management interface
Dispatcher has management interface available by default in /opt/itns/var/run/mgmt.
You can manually add or remove authids and see its status.
```
echo "help" | socat stdio /opt/itns/var/run/mgmt
show authid [authid]
show session [sessionid]
kill session <sessionid>
topup <authid> <itns>
spend <authid> <itns>
add authid <authid> <serviceid>
del authid <authid>
loglevel {DEBUG|INFO|WARNING|ERROR}
refresh
cleanup

```

Example1: Add static authid:
```
echo "add authid authid2 1a" | socat stdio /opt/itns/var/run/mgmt
Added (authid2: serviceid=1a, created=Tue Jul 17 19:39:07 2018,modified=Tue Jul 17 19:39:07 2018, balance=100000.000000, perminute=0.001000, minsleft=100000000.000000, charged_count=1, discharged_count=0

```

Example2: Topup authid:
```
 echo "topup authid2 1" | socat stdio /opt/itns/var/run/mgmt
TopUp (authid2: serviceid=1a, created=Tue Jul 17 19:39:07 2018,modified=Tue Jul 17 19:39:47 2018, balance=100001.000000, perminute=0.001000, minsleft=100001000.000000, charged_count=2, discharged_count=0

```

## Directories

### client
 Everything related to client part. More information [there](client/README.md)
 
### conf
 Example config files and config templates.
 
### server
 Code related to VPN server part.
 
