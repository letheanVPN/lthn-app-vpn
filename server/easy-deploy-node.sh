#!/bin/sh

set -e
set -v

if [ "$USER" = "root" ]; then
    echo "Do not run this as root! It will invoke sudo automatically. Exiting!"
    exit 2
fi

# Set defaults. Can be overriden by env variables
[ -z "$BRANCH" ] && BRANCH=master
[ -z "$CAPASS" ] && CAPASS=1234
[ -z "$CACN" ] && CACN=ITNSFakeNode
[ -z "$ENDPOINT" ] && ENDPOINT="1.2.3.4"
[ -z "$PORT" ] && PORT="8080"
[ -z "$PROVTYPE" ] && PROVTYPE="residential"
[ -z "$WALLET" ] && WALLET="izxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
[ -z "$EMAIL" ] && EMAIL=""

export BRANCH CAPASS CACN ENDPOINT PORT PROVTYPE WALLET EMAIL

(
sudo apt update
sudo apt-get -y upgrade
sudo apt-get install -y joe less mc git python3 python3-pip haproxy openvpn tmux squid
if ! [ -d intense-vpn  ]; then
  git clone https://github.com/valiant1x/intense-vpn.git
  cd intense-vpn
else
  cd intense-vpn
  git pull
fi
git checkout $BRANCH
pip3 install -r requirements.txt
./configure.sh --easy
make install FORCE=1
/opt/itns/bin/itnsdispatcher --provider-type $PROVTYPE \
     --generate-sdp --provider-name FakeProvider --wallet-address "$WALLET" \
     --sdp-service-crt /opt/itns/etc/ca/certs/ha.cert.pem \
     --sdp-service-name proxy --sdp-service-id 1a --sdp-service-fqdn $ENDPOINT --sdp-service-port $PORT \
     --sdp-service-type proxy --sdp-service-cost 0.001 --sdp-service-dlspeed 1 --sdp-service-ulspeed 1 \
     --sdp-service-prepaid-mins 2 --sdp-service-verifications 1

sudo systemctl daemon-reload
sudo systemctl enable squid
if ! sudo grep -q "#https_websocket" /etc/squid/squid.conf; then
    sudo sh <<EOF
echo acl SSL_ports port 80 \#https_websocket >>/etc/squid/squid.conf
echo acl SSL_ports port 8080  \#https_websocket >>/etc/squid/squid.conf
echo acl Safe_ports port 8080 \#http_websockett >>/etc/squid/squid.conf
EOF
fi

sudo systemctl restart squid
sudo systemctl enable itnsdispatcher
sudo systemctl restart itnsdispatcher
sudo systemctl disable haproxy
sudo systemctl stop haproxy

cat /opt/itns/etc/sdp.json
) 2>&1 | tee easy.log 

if [ -n "$EMAIL" ]; then
   cat easy.log | mail -s "VPN node created on $(uname -n)." "$EMAIL"
fi
