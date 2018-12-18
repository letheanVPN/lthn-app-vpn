#!/bin/sh

export PATH=/opt/lthn/bin:/sbin:/usr/sbin:$PATH
export CONF=/opt/lthn/etc/

testvol(){
  if ! touch /opt/lthn/etc/testrw; then
    echo "/opt/lthn/etc is not writable! Mount it to host! Exiting."
    exit 1
  else
    rm -f /opt/lthn/etc/testrw
  fi

  if ! touch /var/log/syslog; then
    echo "/var/log is not writable! Mount it to host! Exiting."
    exit 1
  fi
}

testconf(){
    if ! [ -f /opt/lthn/etc/sdp.json ] || ! [ -f /opt/lthn/etc/dispatcher.ini ]; then
        echo "We are not configured! Exiting! Run easy-deploy first or configure manually"
        exit 1
    fi
}

mkdir -p /var/log/squid
mkdir -p /var/log/zabbix

case $1 in
easy-deploy)
    lethean-wallet-cli --mnemonic-language English --generate-new-wallet $CONF/vpn --daemon-host $DAEMON_HOST --restore-height 254293 --password "$WALLETPASS" --log-file /dev/stdout --log-level 4 --command exit
    WALLET=$(cat $CONF/vpn.address.txt)
    ./configure.sh --prefix "/opt/lthn" --runas-user lthn --runas-group lthn --easy --with-wallet-address "$WALLET" --with-wallet-rpc-user dispatcher --with-wallet-rpc-pass SecretPass $provideropts
    make install FORCE=y
    /opt/lthn/bin/lvmgmt --generate-sdp \
     --sdp-provider-type "$PROVTYPE" \
     --sdp-provider-name EasyProvider \
     --wallet-address "$WALLET" \
     --sdp-service-crt /opt/lthn/etc/ca/certs/ha.cert.pem \
     --sdp-service-name proxy --sdp-service-id 1a --sdp-service-endpoint "$ENDPOINT" --sdp-service-port "$PORT" \
     --sdp-service-type proxy --sdp-service-cost 0.001 --sdp-service-dlspeed 1 --sdp-service-ulspeed 1 \
     --sdp-service-prepaid-mins 10 --sdp-service-verifications 0

if ! sudo grep -q "#https_websocket" /etc/squid/squid.conf; then
    sudo sh <<EOF
echo acl SSL_ports port 80 \#https_websocket >>/etc/squid/squid.conf
echo acl SSL_ports port 8080  \#https_websocket >>/etc/squid/squid.conf
echo acl Safe_ports port 8080 \#http_websockett >>/etc/squid/squid.conf
EOF
  /opt/lthn/bin/lvmgmt --upload-sdp
fi

    ;;
run)
    testvol()
    testconf()
    if [ -x /usr/sbin/zabbix_agentd ]; then
       echo "Starting zabbix agent" >&2
       zabbix_agentd -c /etc/zabbix/zabbix_agentd.conf
    fi
    echo "Starting squid" >&2
    squid 
    if [ -f $CONF/vpn ]; then
      lethean-wallet-vpn-rpc --vpn-rpc-bind-port 14660 --wallet-file $CONF/vpn --daemon-host $DAEMON_HOST --rpc-login 'dispatcher:SecretPass' --password "$WALLETPASS" --log-file /var/log/wallet.log &
      sleep 4
    else
      echo "Wallet is not inside container." >&2
    fi
    echo "Starting dispatcher" >&2
    unset HTTP_PROXY
    unset http_proxy
    shift
    while true; do
        lthnvpnd "$@"
        sleep 3
    done
    ;;
lthnvpnc|lthnvpnd|lvmgmt)
    testvol()
    testconf()
    exec $@
    ;;
lthnvpnd)
    testvol()
    testconf()
    lthnvpnd "$@"
    ;;
lvmgmt)
    testvol()
    exec lvmgmt "$@"
    ;;
root)
    cd /home/lthn
    su --preserve-environment lthn
    ;;
sh|bash)
    /bin/bash
    ;;
*)
    echo "Bad command."
    exit 2
    ;;
esac
