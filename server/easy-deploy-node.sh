#!/bin/sh

set -e
set -v

if [ "$USER" = "root" ]; then
    echo "Do not run this as root! It will invoke sudo automatically. Exiting!"
    exit 2
fi

# Set defaults. Can be overriden by env variables
[ -z "$BRANCH" ] && BRANCH=master
[ -z "$PROVIDERID" ] && PROVIDERID=""
[ -z "$PROVIDERKEY" ] && PROVIDERKEY=""
[ -z "$DAEMON_BIN_URL" ] && DAEMON_BIN_URL="https://itns.s3.us-east-2.amazonaws.com/Cli/Cli_Ubuntu160464bitStaticRelease/431/intensecoin-cli-linux-64bit-HEAD-eab8225.tar.bz2"
[ -z "$DAEMON_HOST" ] && DAEMON_HOST="monitor.intensecoin.com"
[ -z "$WALLETPASS" ] && WALLETPASS="abcd1234"
[ -z "$CAPASS" ] && CAPASS=1234
[ -z "$CACN" ] && CACN=ITNSFakeNode
[ -z "$ENDPOINT" ] && ENDPOINT="1.2.3.4"
[ -z "$PORT" ] && PORT="8080"
[ -z "$PROVTYPE" ] && PROVTYPE="residential"
[ -z "$EMAIL" ] && EMAIL=""

export BRANCH CAPASS CACN ENDPOINT PORT PROVTYPE WALLET EMAIL DAEMON_BIN_URL DAEMON_HOST WALLETPASS PROVIDERID PROVIDERKEY

(
sudo apt update
sudo apt-get -y upgrade
sudo apt-get install -y joe less mc git python3 python3-pip haproxy openvpn tmux squid net-tools

install_wallet(){
  DAEMONBZ2=$(basename $DAEMON_BIN_URL)
  DAEMONDIR=$(basename $DAEMON_BIN_URL .tar.bz2)
  wget -nc -c $DAEMON_BIN_URL && \
  tar -xjvf $DAEMONBZ2 && \
  sudo cp $DAEMONDIR/* /usr/local/bin/ && \
  /usr/local/bin/intense-wallet-cli --mnemonic-language English --generate-new-wallet vpn --daemon-host $DAEMON_HOST --restore-height 254293 --password "$WALLETPASS" --command exit && \
  /usr/local/bin/intense-wallet-rpc --wallet-file ~/vpn --daemon-host $DAEMON_HOST --rpc-bind-port 14660 --rpc-login 'dispatcher:SecretPass' --password "$WALLETPASS" & \
  echo @reboot /usr/local/bin/intense-wallet-rpc --rpc-bind-port 14660 --wallet-file ~/vpn --daemon-host $DAEMON_HOST --rpc-login 'dispatcher:SecretPass' --password "$WALLETPASS" >wallet.crontab && \
  crontab wallet.crontab 
}

if ! [ -f ~/vpn.address.txt ]; then
  install_wallet
fi
WALLET=$(cat ~/vpn.address.txt)

if ! [ -d intense-vpn  ]; then
  git clone https://github.com/valiant1x/intense-vpn.git
  cd intense-vpn
else
  cd intense-vpn
  git pull
fi
git checkout $BRANCH
pip3 install -r requirements.txt
if [ -n "$PROVIDERID" ]; then
  provideropts="--with-providerid $PROVIDERID --with-providerkey $PROVIDERKEY"
fi
./configure.sh --easy --with-wallet-address "$WALLET" --with-wallet-rpc-user dispatcher --with-wallet-rpc-pass SecretPass
make install FORCE=1
/opt/itns/bin/itnsdispatcher --generate-sdp \
     --provider-type $PROVTYPE \
     --provider-name EasyProvider \
     --wallet-address "$WALLET" \
     --sdp-service-crt /opt/itns/etc/ca/certs/ha.cert.pem \
     --sdp-service-name proxy --sdp-service-id 1a --sdp-service-fqdn $ENDPOINT --sdp-service-port $PORT \
     --sdp-service-type proxy --sdp-service-cost 0.001 --sdp-service-dlspeed 1 --sdp-service-ulspeed 1 \
     --sdp-service-prepaid-mins 2 --sdp-service-verifications 0

/opt/itns/bin/itnsdispatcher --upload-sdp

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
