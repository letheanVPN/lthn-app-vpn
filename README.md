# intense-vpn
This repository contains code needed to setup and run Intense Coin Virtual Private Network (VPN).

## Requirements
 * python3
 * python-pickle
 * python-json
 * python-ed25519
 * haproxy
 * openvpn (optional)

## Configure and install
Project is configured by standard configure script. You can change basic parameters of service via this script.
```bash
./configure --help
make
make install
``` 

## Usage 

## Directories

### client
 Everything related to client part. More information [there](client/README.md)
 
### conf
 Example config files. More information [there](conf/README.md)
 
### server
 Code ralated to VPN server part. More information [there](server/README.md)
 

