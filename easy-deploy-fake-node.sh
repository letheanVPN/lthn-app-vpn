#!/bin/sh

set -e
set -v

sudo apt update
sudo apt-get install -y joe less mc git python3 python3-pip haproxy openvpn tmux squid
if ! [ -d intense-vpn  ]; then
  git clone https://github.com/valiant1x/intense-vpn.git
  git checkout config-sdp
else
  cd intense-vpn
  git pull
  cd ..
fi
cd intense-vpn
git checkout config-sdp
pip3 install -r requirements.txt
./configure.sh  --runas-user "$USER" --with-capass 1234  --with-cn 'ITNSFakeNode' --generate-ca --generate-dh
sudo make install
cp conf/dispatcher_example.json /opt/itns/etc/dispatcher.json
cp conf/sdp_example.json /opt/itns/etc/sdp.json
/opt/itns/bin/itnsdispatcher -d DEBUG --generate-configs
sed -i 's#hdr(X-ITNS-PaymentID) -u#hdr(X-ITNS-PaymentID) -f /tmp/authids -u#' /opt/itns//var/proxy_1A//cfg
sed -i 's#/opt/itns//var/log#/dev/log#' /opt/itns//var/proxy_1A//cfg
echo authid1 >/tmp/authids
echo authid2 >>/tmp/authids
echo authid3 >>/tmp/authids

sudo cp /tmp/itnsvpn.service /etc/systemd/system/itnsvpn.service
sudo systemctl daemon-reload
sudo systemctl enable squid
sudo systemctl start squid
/usr/sbin/haproxy -Ds -p /opt/itns//var/proxy_1A//pid -f /opt/itns//var/proxy_1A//cfg
