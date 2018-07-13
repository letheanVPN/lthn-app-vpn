#!/bin/sh

set -e
set -v

# Set defaults. Can be overriden by env variables
[ -z "$BRANCH" ] && BRANCH=master
[ -z "$CAPASS" ] && CAPASS=1234
[ -z "$CACN" ] && CACN=ITNSFakeNode
[ -z "$ENDPOINT" ] && ENDPOINT="1.2.3.4"
[ -z "$PORT" ] && PORT="8080"
[ -z "$PROVTYPE" ] && PROVTYPE="residental"
[ -z "$WALLET" ] && WAllet="izxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
[ -z "$EMAIL" ] && EMAIL=""

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
./configure.sh  --runas-user "$USER" --with-capass "$CAPASS"  --with-cn "$CACN" --generate-ca --generate-dh --install-service
make install
/opt/itns/bin/itnsdispatcher --generate-providerid /opt/itns/etc/provider
providerid=$(cat /opt/itns/etc/provider.public)
/opt/itns/bin/itnsdispatcher --sdp-provider-type $PROVTYPE \
     --generate-sdp --sdp-provider-id "$providerid" \
     --sdp-provider-name FakeProvider --sdp-wallet-address "$WALLET" \
     --sdp-provider-ca /opt/itns/etc/ca/certs/ca.cert.pem --sdp-service-crt /opt/itns/etc/ca//certs/ha.cert.pem \
     --sdp-service-name proxy --sdp-service-id 1a --sdp-service-fqdn $ENDPOINT --sdp-service-port $PORT \
     --sdp-service-type proxy --sdp-service-cost 0.001 --sdp-service-dlspeed 1 --sdp-service-ulspeed 1 \
     --sdp-service-prepaid-mins 2 --sdp-service-verifications 1

/opt/itns/bin/itnsdispatcher -d DEBUG --generate-server-configs

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

cat /opt/itns/etc/sdp.json

if [ -n "$EMAIL" ]; then
   cat /opt/itns/etc/sdp.json | mail -s "VPN node created. See SDP in email." "$EMAIL"
fi