#!/bin/sh

set -e
set -v

if [ "$USER" = "root" ]; then
    echo "Do not run this as root! It will invoke sudo automatically. Exiting!"
    exit 2
fi

# Set defaults. Can be overriden by env variables
[ -z "$LTHNPREFIX" ] && LTHNPREFIX=/opt/lthn
[ -z "$BRANCH" ] && BRANCH=master
[ -z "$PROVIDERID" ] && PROVIDERID=""
[ -z "$PROVIDERKEY" ] && PROVIDERKEY=""
[ -z "$DAEMON_BIN_URL" ] && DAEMON_BIN_URL="https://itns.s3.us-east-2.amazonaws.com/Cli/Cli_Ubuntu160464bitStaticRelease/1755/lethean-cli-linux-64bit-v3.0.0.b3.tar.bz2"
[ -z "$DAEMON_HOST" ] && DAEMON_HOST="sync.lethean.io"
[ -z "$WALLETPASS" ] && WALLETPASS="abcd1234"
[ -z "$CAPASS" ] && CAPASS=1234
[ -z "$CACN" ] && CACN=ITNSFakeNode
[ -z "$ENDPOINT" ] && ENDPOINT="1.2.3.4"
[ -z "$PORT" ] && PORT="8080"
[ -z "$PROVTYPE" ] && PROVTYPE="residential"
[ -z "$EMAIL" ] && EMAIL=""
[ -z "$ZABBIX_SERVER" ] && ZABBIX_SERVER=""
[ -z "$ZABBIX_HOSTNAME" ] && ZABBIX_HOSTNAME=$(uname -n)
[ -z "$ZABBIX_META" ] && ZABBIX_META="LETHEANNODE"

export LTHNPREFIX BRANCH CAPASS CACN ENDPOINT PORT PROVTYPE WALLET EMAIL DAEMON_BIN_URL DAEMON_HOST WALLETPASS PROVIDERID PROVIDERKEY ZABBIX_SERVER ZABBIX_PSK ZABBIX_PORT ZABBIX_META USER HOME HTTP_PROXY HTTPS_PROXY

(
sudo -E apt-get update
sudo -E apt-get -y upgrade
sudo -E apt-get install -y joe less mc git python3 python3-pip haproxy openvpn tmux squid net-tools wget

sysctl(){
  if which systemctl >/dev/null; then
    sudo systemctl $1 $2 $3 $4
  fi
}

install_wallet(){
  DAEMONBZ2=$(basename $DAEMON_BIN_URL)
  DAEMONDIR=$(basename $DAEMON_BIN_URL .tar.bz2)
  sudo mkdir -p $LTHNPREFIX/bin /etc/systemd/system && \
  sudo chown $USER $LTHNPREFIX/bin && \
  wget -nc -c $DAEMON_BIN_URL && \
  sudo tar --strip-components 1 -C $LTHNPREFIX/bin/ -xjvf $DAEMONBZ2 && \
  sudo cp conf/letheand.service /etc/systemd/system/ && \
  sudo cp conf/letheand.env /etc/default/letheand && \
  sudo cp conf/lethean-wallet-vpn-rpc.service /etc/systemd/system/ && \
  cp conf/lethean-wallet-vpn-rpc.env wallet.env && \
  $LTHNPREFIX/bin/lethean-wallet-cli --mnemonic-language English --generate-new-wallet $HOME/vpn --daemon-host $DAEMON_HOST --restore-height 254293 --password "$WALLETPASS" --log-file /dev/stdout --log-level 4 --command exit && \
  echo LETHEANVPNRPC_ARGS="--vpn-rpc-bind-port 14660 --wallet-file $HOME/vpn --daemon-host $DAEMON_HOST --rpc-login 'dispatcher:SecretPass' --password '$WALLETPASS' --log-file $HOME/wallet.log" >>wallet.env && \
  echo cd $HOME >>wallet.env && \
  sudo cp wallet.env /etc/default/lethean-wallet-vpn-rpc
  sudo sed -i "s^User=lthn^User=$USER^" /etc/systemd/system/letheand.service
  sudo sed -i "s^User=lthn^User=$USER^" /etc/systemd/system/lethean-wallet-vpn-rpc.service
  sysctl daemon-reload
  sysctl enable lethean-wallet-vpn-rpc
  sysctl start lethean-wallet-vpn-rpc
}

install_zabbix(){
  wget https://repo.zabbix.com/zabbix/4.0/debian/pool/main/z/zabbix-release/zabbix-release_4.0-2+stretch_all.deb
  sudo dpkg -i zabbix-release_4.0-2+stretch_all.deb
  sudo apt-get update
  sudo apt-get install -y zabbix-agent zabbix-sender
  sudo sed -i "s/Server=(.*)/Server=$ZABBIX_SERVER" /etc/zabbix/zabbix_agentd.conf
  sudo sed -i "s/ServerActive=(.*)/ServerActive=$ZABBIX_SERVER" /etc/zabbix/zabbix_agentd.conf
  sudo sed -i "s/Hostname=(.*)/Hostname=$ZABBIX_HOSTNAME" /etc/zabbix/zabbix_agentd.conf
  sudo sed -i "s/HostMetadata=(.*)/HostMetadata=$ZABBIX_META" /etc/zabbix/zabbix_agentd.conf
  sysctl daemon-reload
  sysctl enable zabbix-agent
  sysctl start zabbix-agent
}

if [ -f lthnvpnd.py ] || [ -f server/lthnvpnd.py ]; then  
  # We are already in dev directory
  if [ -f lthnvpnd.py ];  then
     cd ..
  fi
else
  if ! [ -d lethean-vpn  ]; then
    git clone https://github.com/LetheanMovement/lethean-vpn.git
    cd lethean-vpn
  else
    cd lethean-vpn
    git pull
  fi
  git checkout $BRANCH
fi

if ! [ -f $HOME/vpn.address.txt ]; then
  install_wallet
fi
WALLET=$(cat $HOME/vpn.address.txt)

if [ -n "$ZABBIX_SERVER" ]; then
  install_zabbix
fi

pip3 install -r requirements.txt
if [ -n "$PROVIDERID" ]; then
  provideropts="--with-providerid $PROVIDERID --with-providerkey $PROVIDERKEY"
fi
./configure.sh --prefix "$LTHNPREFIX" --easy --with-wallet-address "$WALLET" --with-wallet-rpc-user dispatcher --with-wallet-rpc-pass SecretPass $provideropts
make install FORCE=1
$LTHNPREFIX/bin/lvmgmt --generate-sdp \
     --provider-type $PROVTYPE \
     --provider-name EasyProvider \
     --wallet-address "$WALLET" \
     --sdp-service-crt $LTHNPREFIX/etc/ca/certs/ha.cert.pem \
     --sdp-service-name proxy --sdp-service-id 1a --sdp-service-fqdn $ENDPOINT --sdp-service-port $PORT \
     --sdp-service-type proxy --sdp-service-cost 0.001 --sdp-service-dlspeed 1 --sdp-service-ulspeed 1 \
     --sdp-service-prepaid-mins 10 --sdp-service-verifications 0

sysctl daemon-reload
sysctl enable squid
if ! sudo grep -q "#https_websocket" /etc/squid/squid.conf; then
    sudo sh <<EOF
echo acl SSL_ports port 80 \#https_websocket >>/etc/squid/squid.conf
echo acl SSL_ports port 8080  \#https_websocket >>/etc/squid/squid.conf
echo acl Safe_ports port 8080 \#http_websockett >>/etc/squid/squid.conf
EOF
fi

sysctl restart squid
sysctl enable lthnvpnd
sysctl restart lthnvpnd
sysctl disable haproxy
sysctl stop haproxy

cat /opt/lthn/etc/sdp.json
$LTHNPREFIX/bin/lvmgmt --upload-sdp

) 2>&1 | tee easy.log 

if [ -n "$EMAIL" ]; then
   cat easy.log | mail -s "VPN node created on $(uname -n)." "$EMAIL"
fi
