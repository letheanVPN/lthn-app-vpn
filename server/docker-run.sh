#!/bin/sh

export PATH=$LTHNPREFIX/bin:/sbin:/usr/sbin:$PATH
export CONF=$LTHNPREFIX/etc/

case $1 in
easy-deploy)
    lethean-wallet-cli --mnemonic-language English --generate-new-wallet $CONF/vpn --daemon-host $DAEMON_HOST --restore-height 254293 --password "$WALLETPASS" --log-file /dev/stdout --log-level 4 --command exit
    WALLET=$(cat $CONF/vpn.address.txt)
    ./configure.sh --prefix "$LTHNPREFIX" --easy --with-wallet-address "$WALLET" --with-wallet-rpc-user dispatcher --with-wallet-rpc-pass SecretPass $provideropts
    make install FORCE=y
    $LTHNPREFIX/bin/lvmgmt --generate-sdp \
     --provider-type $PROVTYPE \
     --provider-name EasyProvider \
     --wallet-address "$WALLET" \
     --sdp-service-crt $LTHNPREFIX/etc/ca/certs/ha.cert.pem \
     --sdp-service-name proxy --sdp-service-id 1a --sdp-service-fqdn $ENDPOINT --sdp-service-port $PORT \
     --sdp-service-type proxy --sdp-service-cost 0.001 --sdp-service-dlspeed 1 --sdp-service-ulspeed 1 \
     --sdp-service-prepaid-mins 10 --sdp-service-verifications 0

if ! sudo grep -q "#https_websocket" /etc/squid/squid.conf; then
    sudo sh <<EOF
echo acl SSL_ports port 80 \#https_websocket >>/etc/squid/squid.conf
echo acl SSL_ports port 8080  \#https_websocket >>/etc/squid/squid.conf
echo acl Safe_ports port 8080 \#http_websockett >>/etc/squid/squid.conf
EOF
  $LTHNPREFIX/bin/lvmgmt --upload-sdp
fi

    ;;
run)
    if which zabbix_agentd; then
       echo "Starting zabbix agent" >&2
       zabbix_agentd -c /etc/zabbix/zabbix_agentd.conf
    fi
    echo "Starting squid" >&2
    squid 
    if [ -f $HOME/vpn ]; then
      lethean-wallet-vpn-rpc --vpn-rpc-bind-port 14660 --wallet-file $HOME/vpn --daemon-host $DAEMON_HOST --rpc-login 'dispatcher:SecretPass' --password '$WALLETPASS' --log-file $HOME/wallet.log
    else
      echo "Wallet is not inside container." >&2
    fi
    echo "Starting dispatcher" >&2
    lthnvpnd 
    ;;
lthnvpnc|lthnvpnd|lvmgmt)
    exec $@
    ;;
lthnvpnd)
    exec lthnvpnd "$@"
    ;;
lvmgmt)
    exec lvmgmt "$@"
    ;;
root)
    cd /home/lthn
    su --preserve-environment lthn
    ;;
sh)
    /bin/bash
    ;;
*)
    echo "Bad command."
    exit 2
    ;;
esac
