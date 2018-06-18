# intense-vpn
This repository contains code needed to setup and run Intense Coin Virtual Private Network (VPN).

## Requirements
 * python3
 * python3-pip
 * haproxy
 * openvpn (optional)

There are more required python classes but they will be installed
automatically during install.

On debian, use standard packager:
```bash
sudo apt-get install python3 python3-pip haproxy
```

## Configure and install
Project is configured by standard configure script. You can change basic parameters of service via this script.
```bash
pip3 install -r requirements.txt
./configure.sh [--openvpn-bin bin] [--openssl-bin bin] [--haproxy-bin bin] [--python-bin bin] [--pip-bin bin] [--runas-user user] [--runas-group group] [--prefix prefix] [--with-capass pass] [--generate-ca] [--generate-dh]
make ca PASS="<yourprivatepassword>"
cp conf/dispatcher_example.json /opt/itns/etc/dispatcher.json
cp conf/sdp_example.json /opt/itns/etc/sdp.json
sudo make install
``` 

Please edit configs because examples will not work for you. You have to
prepare at least SDP with your own services!

## WARNING: Runs as root
By default, the script uses `root` as the run as group/user. This is a large security risk and should never be used in production!

## Usage 

## Directories

### client
 Everything related to client part. More information [there](client/README.md)
 
### conf
 Example config files. More information [there](conf/README.md)
 
### server
 Code ralated to VPN server part. More information [there](server/README.md)
 

