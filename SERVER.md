# Lethean VPN daemon
This repository contains code needed to setup and run an exit node on the Lethean Virtual Private Network (VPN).

**The exit node is currently only supported on Linux.**

## Design
ITNS (aka LTHN) VPN dispatcher is a tool that orchestrates all other modules (proxy, VPN, config, etc.). It does not provide any VPN functionality by itself.
The dispatcher uses system packages whenever possible but it runs all instances manually after invoking. 
The dispatcher has two distinct modes of operation: proxy and VPN.

### Proxy mode (mandatory)
In proxy mode, it runs a preconfigured instance of haproxy which acts as frontend for clients (authenticated by ITNS payments), and uses another HTTP proxy as the backend.
Squid is the simplest HTTP proxy to use as a backend, but any other HTTP proxy would work fine as well. Easy-deploy scripts autoconfigure squid as the backend.

### VPN mode (optional)
If you decide to run ITNS VPN dispatcher in VPN mode, it starts an OpenVPN server authenticated by ITNS payments.

### Session management
The dispatcher orchestrates all proxy and VPN instances by managing authentication and session creation. 
In huge sites, this could generate significant load. Session management can be turned off. In such cases, sessions which are alive after a client's payment is spent will not be terminated automatically.

## Requirements
 * python3
 * python3-pip
 * haproxy
 * squid or other HTTP proxy
 * openvpn (optional)
 * sudo installed and configured

There are more required python classes but they will be installed automatically during install.

On debian, use standard packager:
```bash
sudo apt-get install python3 python3-pip haproxy

```

## Configure and install
The dispatcher is configured by a standard configure script. You can change basic parameters of proxy or VPN services via this script. It will ask you for all parameters and generate sdp.json and dispatcher.ini. Please note that config files will be generic and it is good to review and edit them before real usage. You can run the configure script again if you want to change parameters but you have to run *make clean* first.

If you use *FORCE=1* during `make install`, it will overwrite your configs and certificates/keys. Without this flag, all configs and keys are left untouched.

### Wallet
The dispatcher requires having a valid Lethean wallet configured before running, it requires having the wallet-vpn-rpc binary runing. Please note that there are two passwords passed to initialize the wallet-vpn-rpc binary; one for unlocking the wallet and one for dispatcher RPC calls.
You can download these binaries from [here](https://itns.s3.us-east-2.amazonaws.com/Cli/Cli_Ubuntu160464bitStaticRelease/697/lethean-cli-linux-64bit-letheanize-e45d13b.tar.bz2), or build from source using [lethean master](https://github.com/LetheanMovement/lethean/tree/master).
wallet-vpn-rpc initialization:
```bash
lethean-wallet-vpn-rpc --vpn-rpc-bind-port 13660 --wallet-file itnsvpn --rpc-login
dispatcher:<somepassword> --password <walletpassword>

```

Note that using the `lethean-wallet-vpn-rpc` binary as described also requires having the `letheand` daemon running, or using a remote daemon. If you would prefer to use a remote daemon instead of running a daemon locally, we recommend using the Lethean team hosted node at **sync.lethean.io**
```bash
lethean-wallet-vpn-rpc --daemon-host sync.lethean.io
```

### Basic install
See ./configure.sh --help for more fine-tuned options
```bash
git clone https://github.com/LetheanMovement/lethean-vpn.git
cd lethean-vpn
pip3 install -r requirements.txt
./configure.sh --easy [--with-wallet-address <wallet_address>]
make install [FORCE=1]
```

### Public configuration - sdp.json
*/opt/itns/etc/sdp.json* describes local services for orchestration. It is uploaded to SDP server by --upload-sdp option. Note that uploading to SDP server is paid service. <!--  **TODO add SDP server integration instructions** --> 
After installation, you will be instructed to generate the sdp.json file, which is required to run the dispatcher.
You can either answer questions using the wizard (*--generate-sdp*) or you can use cmdline params to set defaults. See help.
```bash
/opt/itns/bin/lthnvpnd --generate-sdp --wallet-address some_wallet_address [--sdp-service-name someName] ...

```

You may need to invoke lthnvpnd using `python3` if you receive dependency errors. If you opted to use the `--runas-user` and `--runas-group` setup params, you will also need to `su -` to that user or use `sudo` when using the dispatcher.
```bash
[su - vpnuser]
python3 /opt/itns/bin/lthnvpnd ...
```

### Private configuration - dispatcher.ini
*/opt/itns/etc/dispatcher.ini* is a local file containing private information needed to run the  dispatcher. Do not upload it anywhere or share it with anyone as it contains private keys. You should also create a backup of this file.
By default, *make install* will generate a default file for you but you need to configure it to suit your needs.
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
Never run this on a system already configured for lthnvpnd! It will overwrite config files!
```bash
wget https://raw.githubusercontent.com/LetheanMovement/lethean-vpn/master/server/easy-deploy-node.sh
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
[ -z "$PROVTYPE" ] && PROVTYPE="residential"
[ -z "$WALLET" ] && WALLET="izxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
[ -z "$EMAIL" ] && EMAIL=""

```

## Usage 
```bash
 /opt/itns/bin/lthnvpnd -h
usage: lthnvpnd [-f CONFIGFILE] [-h] [-s SDPFILE] [-p PIDFILE]
                      [-l LEVEL] [-A FILE] [-a FILE] [--refresh-time SEC]
                      [--save-time SEC] [--max-wait-to-spend SEC] [-lc FILE]
                      [-v] [-G PREFIX] [--run-services RUNSERVICES]
                      [--track-sessions TRACKSESSIONS] [-S] [-C SERVICEID]
                      [-D] [-E] [-U] [--sdp-service-crt FILE]
                      [--sdp-service-type TYPE] [--sdp-service-fqdn FQDN]
                      [--sdp-service-port NUMBER] [--sdp-service-name NAME]
                      [--sdp-service-id NUMBER] [--sdp-service-cost ITNS]
                      [--sdp-service-disable NUMBER]
                      [--sdp-service-refunds NUMBER]
                      [--sdp-service-dlspeed Mbps]
                      [--sdp-service-ulspeed Mbps]
                      [--sdp-service-prepaid-mins TIME]
                      [--sdp-service-verifications NUMBER] --ca ca.crt
                      --wallet-address ADDRESS [--wallet-rpc-uri URI]
                      [--wallet-username USER] [-H HEIGHT]
                      [--wallet-password PW] [--sdp-uri URL] --provider-id
                      PROVIDERID --provider-key PROVIDERKEY --provider-name
                      NAME [--provider-type TYPE] [--provider-terms TEXT]

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
  -p PIDFILE, --pid PIDFILE
                        PID file (default:
                        /opt/itns//var/run/lthnvpnd.pid)
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
  --max-wait-to-spend SEC
                        When payment arrive, we will wait max this number of
                        seconds for first session before spending credit.
                        (default: 1800)
  -lc FILE, --logging-conf FILE
                        Logging config file (default: None)
  -v, --verbose         Be more verbose on output (default: None)
  -G PREFIX, --generate-providerid PREFIX
                        Generate providerid files (default: None)
  --run-services RUNSERVICES
                        Run services from dispatcher or externally. Default to
                        run by lthnvpnd. (default: True)
  --track-sessions TRACKSESSIONS
                        If true, dispatcher will track sessions. If not,
                        existing sessions will not be terminated after payment
                        is spent. (default: True)
  -S, --generate-server-configs
                        Generate configs for services and exit (default: None)
  -C SERVICEID, --generate-client-config SERVICEID
                        Generate client config for specified service on stdout
                        and exit (default: None)
  -D, --generate-sdp    Generate SDP by wizzard (default: None)
  -E, --edit-sdp        Edit existing SDP config (default: None)
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
  --wallet-address ADDRESS
                        Wallet address (default: None)
  --wallet-rpc-uri URI  Wallet URI (default: http://127.0.0.1:13660/json_rpc)
  --wallet-username USER
                        Wallet username (default: dispatcher)
  -H HEIGHT, --from-height HEIGHT
                        Initial height to start scan payments. Default is
                        actual height. (default: -1)
  --wallet-password PW  Wallet passwd (default: None)
  --sdp-uri URL         SDP server(s) (default: https://slsf2fy3eb.execute-
                        api.us-east-1.amazonaws.com/qa/v1)
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
The dispatcher has a management interface available by default in */opt/itns/var/run/mgmt*.
You can manually add or remove authids and query its status.
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

Example 1: Show sessions:
```
echo "show session" | socat stdio /opt/itns/var/run/mgmt
Added (authid2: serviceid=1a, created=Tue Jul 17 19:39:07 2018,modified=Tue Jul 17 19:39:07 2018, balance=100000.000000, perminute=0.001000, minsleft=100000000.000000, charged_count=1, discharged_count=0

```

Example 2: Topup authid:
```
 echo "topup 1abbcc 1" | socat stdio /opt/itns/var/run/mgmt
TopUp (1abbcc: serviceid=1a, created=Tue Jul 17 19:39:07 2018,modified=Tue Jul 17 19:39:47 2018, balance=100001.000000, perminute=0.001000, minsleft=100001000.000000, charged_count=2, discharged_count=0

```

## Updating the dispatcher

To update the dispatcher, run the following commands from the directory that the lethean-vpn repo was initialized in:
```
git pull
./configure.sh --easy
make install
rm -f /opt/itns/var/authids.db
sudo systemctl daemon-reload
sudo systemctl restart lthnvpnd
```

## Directories

### client
 Everything related to client part. More information [there](client/README.md)
 
### conf
 Example config files and config templates.
 
### server
 Code related to VPN server part.
 
