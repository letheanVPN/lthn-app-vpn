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
sudo apt-get install python3 python3-pip haproxy sudo
```

## Configure and install
Project is configured by standard configure script. You can change basic parameters of service via this script.
It will ask you for all parameters and generate sdp.json and dispatcher.ini. 
Please note that config files will be generic and it is good to review and
edit them before real usage. You can run configure script more times if
you want to change parameters but you have to do *make clean* first.
If you use *FORCE=1* during make install, it will overwrite your configs.
Without this flag, all configs and keys are left untouched.
```bash
pip3 install -r requirements.txt
./configure.sh --with-capass 'SomePass' --with-cn 'someCommonName' --generate-ca --generate-dh --runas-user "$USER" --generate-sdp --install-service
make install [FORCE=1]
``` 
For fully automated install, please use our easy deploy script. Please note that this script works only if system is clean and sudo is already configured for user which runs this.
You can use more env variables to tune parameters. See script header for available env variables:

```
[ -z "$BRANCH" ] && BRANCH=master
[ -z "$CAPASS" ] && CAPASS=1234
[ -z "$CACN" ] && CACN=ITNSFakeNode
[ -z "$ENDPOINT" ] && ENDPOINT="1.2.3.4"
[ -z "$PORT" ] && PORT="8080"
[ -z "$PROVTYPE" ] && PROVTYPE="residental"
[ -z "$WALLET" ] && WALLET="izxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
[ -z "$EMAIL" ] && EMAIL=""
```

Never run this on configured system! It will overwrite config files!
```
wget https://raw.githubusercontent.com/valiant1x/intense-vpn/config-sdp/server/easy-deploy-node.sh
chmod +x easy-deploy-node.sh
BRANCH=config-sdp ./easy-deploy-node.sh
```

## Usage 
```
/opt/itns/bin/itnsdispatcher -h
usage: itnsdispatcher [-h] [-f CONFIGFILE] [-s SDPFILE] [-d LEVEL] [-G PREFIX]
                      [-S] [-C SERVICEID] [-D] [--sdp-provider-type TYPE]
                      [--sdp-provider-id ID] [--sdp-provider-name NAME]
                      [--sdp-wallet-address ADDR] [--sdp-provider-terms TEXT]
                      [--sdp-provider-ca FILE] [--sdp-service-crt FILE]
                      [--sdp-service-type TYPE] [--sdp-service-fqdn FQDN]
                      [--sdp-service-port NUMBER] [--sdp-service-name NAME]
                      [--sdp-service-id NUMBER] [--sdp-service-cost ITNS]
                      [--sdp-service-refunds NUMBER]
                      [--sdp-service-dlspeed Mbps]
                      [--sdp-service-ulspeed Mbps]
                      [--sdp-service-prepaid-mins TIME]
                      [--sdp-service-verifications NUMBER]

optional arguments:
  -h, --help            show this help message and exit
  -f CONFIGFILE, --config CONFIGFILE
                        Config file (default: /opt/itns//etc/dispatcher.json)
  -s SDPFILE, --sdp SDPFILE
                        SDP file (default: /opt/itns//etc/sdp.json)
  -d LEVEL, --debug LEVEL
                        Debug level (default: WARNING)
  -G PREFIX, --generate-providerid PREFIX
                        Generate providerid files (default: None)
  -S, --generate-server-configs
                        Generate configs for services and exit (default: None)
  -C SERVICEID, --generate-client-config SERVICEID
                        Generate client config for specified service on stdout
                        and exit (default: None)
  -D, --generate-sdp    Generate SDP by wizzard (default: None)
  --sdp-provider-type TYPE
                        Provider type (for SDP edit/creation only) (default:
                        commercial)
  --sdp-provider-id ID  Provider ID (for SDP edit/creation only) (default:
                        None)
  --sdp-provider-name NAME
                        Provider Name (for SDP edit/creation only) (default:
                        None)
  --sdp-wallet-address ADDR
                        Wallet address (for SDP edit/creation only) (default:
                        None)
  --sdp-provider-terms TEXT
                        Provider terms (for SDP edit/creation only) (default:
                        None)
  --sdp-provider-ca FILE
                        Provider CA file (for SDP edit/creation only)
                        (default: None)
  --sdp-service-crt FILE
                        Provider Proxy crt (for SDP edit/creation only)
                        (default: None)
  --sdp-service-type TYPE
                        Provider VPN crt (for SDP edit/creation only)
                        (default: None)
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
  --sdp-service-refunds NUMBER
                        Allow refunds for Service (for SDP service
                        edit/creation only) (default: None)
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
```

## Directories

### client
 Everything related to client part. More information [there](client/README.md)
 
### conf
 Example config files and config templates.
 
### server
 Code related to VPN server part.
 
