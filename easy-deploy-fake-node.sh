#!/bin/sh

set -e
set -v

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
git checkout config-sdp
pip3 install -r requirements.txt
./configure.sh  --runas-user "$USER" --with-capass 1234  --with-cn 'ITNSFakeNode' --generate-ca --generate-dh
sudo make install
/opt/itns/bin/itnsdispatcher --generate-providerid /opt/itns/etc/provider
providerid=$(cat /opt/itns/etc/provider.public)
/opt/itns/bin/itnsdispatcher --sdp-provider-type residential \
     --generate-sdp --sdp-provider-id "$providerid" \
     --sdp-provider-name FakeProvider --sdp-wallet-address izxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
     --sdp-provider-ca /opt/itns/etc/ca/certs/ca.cert.pem --sdp-service-crt /opt/itns/etc/ca//certs/ha.cert.pem \
     --sdp-service-name fakeproxy --sdp-service-id 1a --sdp-service-fqdn 1.2.3.4 --sdp-service-port 40000 \
     --sdp-service-type proxy --sdp-service-cost 0.001 --sdp-service-dlspeed 1 --sdp-service-ulspeed 1 \
     --sdp-service-prepaid-mins 2 --sdp-service-verifications 1

/opt/itns/bin/itnsdispatcher -d DEBUG --generate-server-configs

sed -i 's#hdr(X-ITNS-PaymentID) -u#hdr(X-ITNS-PaymentID) -f /tmp/authids -u#' /opt/itns//var/proxy_1A//cfg
sed -i 's#/opt/itns//var/log#/dev/log#' /opt/itns//var/proxy_1A//cfg
echo authid1 >/tmp/authids
echo authid2 >>/tmp/authids
echo authid3 >>/tmp/authids

sudo cp /tmp/itnsvpn.service /etc/systemd/system/itnsvpn.service
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

