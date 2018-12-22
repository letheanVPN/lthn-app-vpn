#!/bin/bash

export PATH=/opt/lthn/bin:/sbin:/usr/sbin:$PATH
export CONF=/opt/lthn/etc/

errorExit(){
    echo "$2" >&2
    echo "Exiting with return code $1" >&2
    exit $1
}

prepareClientConf(){
    if ! [ -f /opt/lthn/etc/dispatcher.ini ]; then
cat >/opt/lthn/etc/dispatcher.ini <<EOF
[global]
; 
EOF
    fi
}

testServerConf(){
    if ! [ -f /opt/lthn/etc/sdp.json ] || ! [ -f /opt/lthn/etc/dispatcher.ini ]; then
        errorExit 1 "We are not configured! Exiting! Run easy-deploy first or configure manually"
    fi
}

prepareSquid(){
cat >$CONF/squid.conf <<EOF
acl SSL_ports port 443
acl Safe_ports port 80          # http
acl Safe_ports port 21          # ftp
acl Safe_ports port 443         # https
acl Safe_ports port 70          # gopher
acl Safe_ports port 210         # wais
acl Safe_ports port 1025-65535  # unregistered ports
acl Safe_ports port 280         # http-mgmt
acl Safe_ports port 488         # gss-http
acl Safe_ports port 591         # filemaker
acl Safe_ports port 777         # multiling http
acl Safe_ports port 8080
acl SSL_ports port 8443
acl SSL_ports port 8080
acl SSL_ports port 80
acl CONNECT method CONNECT
acl localnet dst 172.16.0.0/12
acl localnet dst 192.168.0.0/16
acl localnet dst 10.0.0.0/8
access_log syslog:local0.info squid
cache_log /dev/null
http_access deny !Safe_ports
http_access deny CONNECT !SSL_ports
http_access deny localnet
http_access allow localhost manager
http_access deny manager
http_access allow localhost
http_access deny all
http_port 3128
coredump_dir /var/spool/squid
refresh_pattern ^ftp:           1440    20%     10080
refresh_pattern ^gopher:        1440    0%      1440
refresh_pattern -i (/cgi-bin/|\?) 0     0%      0
refresh_pattern .               0       20%     4320
EOF
}

prepareZabbix(){
cat >$CONF/zabbix_agentd.conf <<EOF
PidFile=/opt/lthn/var/run/zabbix_agentd.pid
LogFile=/dev/null
LogFileSize=0
Server=127.0.0.1
ServerActive=127.0.0.1
HostnameItem=system.hostname
EOF
}

case $1 in
easy-deploy)
    lethean-wallet-cli --mnemonic-language English --generate-new-wallet $CONF/vpn --daemon-host $DAEMON_HOST \
       --restore-height 254293 --password "$WALLETPASS" --log-file /dev/stdout --log-level 4 --command exit \
         || { errorExit 2 "Cannot create Wallet file! "; }
    WALLET=$(cat $CONF/vpn.address.txt)
    ./configure.sh --prefix "/opt/lthn" --runas-user lthn --runas-group lthn --easy --with-wallet-address "$WALLET" \
       --with-wallet-rpc-user dispatcher --with-wallet-rpc-pass SecretPass $provideropts \
         || { errorExit 3 "Cannot configure! Something is wrong."; }
    make install FORCE=y || { errorExit 4 "Cannot install! Something is wrong."; }
    /opt/lthn/bin/lvmgmt --generate-sdp \
     --sdp-provider-type "$PROVTYPE" \
     --sdp-provider-name EasyProvider \
     --wallet-address "$WALLET" \
     --sdp-service-crt /opt/lthn/etc/ca/certs/ha.cert.pem \
     --sdp-service-name proxy --sdp-service-id 1a --sdp-service-endpoint "$ENDPOINT" --sdp-service-port "$PORT" \
     --sdp-service-type proxy --sdp-service-cost 0.001 --sdp-service-dlspeed 1 --sdp-service-ulspeed 1 \
     --sdp-service-prepaid-mins 10 --sdp-service-verifications 0 || \
       { errorExit 5 "Cannot create initial SDP!"; }
    ;;

upload-sdp)
    /opt/lthn/bin/lvmgmt --upload-sdp
    ;;

lthnvpnd|run)
    testServerConf
    if ! [ -f $CONF/zabbix_agentd.conf.conf ]; then
      prepareZabbix || { errorExit 2 "Cannot create $CONF/zabbix_agentd.conf! "; }
    fi
    if [ -x /usr/sbin/zabbix_agentd ]; then
       echo "Starting zabbix agent" >&2
       zabbix_agentd -c /etc/zabbix/zabbix_agentd.conf
    fi
    if ! [ -f $CONF/squid.conf ]; then
      prepareSquid || { errorExit 2 "Cannot create $CONF/squid.conf! "; }
    fi
    echo "Starting squid -f $CONF/squid.conf" >&2
    squid -f $CONF/squid.conf
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
    while ! curl http://localhost:14660; do
        echo "Waiting for walet rpc server."
        sleep 5
    done
    exec lthnvpnd "$@"
    ;;

connect)
    prepareClientConf || { errorExit 2 "Cannot create $CONF/dispatcher.ini! "; }
    shift
    exec lthnvpnc connect "$@"
    ;;

list)
    prepareClientConf || { errorExit 2 "Cannot create $CONF/dispatcher.ini! "; }
    shift
    exec lthnvpnc list "$@"
    ;;

lvmgmt)
    shift
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
