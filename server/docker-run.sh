#!/bin/bash

export PATH=/opt/lthn/bin:/sbin:/usr/sbin:$PATH
export CONF=/opt/lthn/etc/
export HOME=/home/lthn
export LMDB=/home/lthn/.intensecoin/lmdb

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

prepareRsyncConf(){
    if ! [ -f $CONF/rsyncd.conf ]; then
      cat >$CONF/rsyncd.conf <<EOF
 [lmdb]
    path = $LMDB
    comment = Lethean Blockchain
    read only = yes
EOF
fi
}

prepareLmdb(){
  if ! [ -d "$LMDB" ] || [ "$1" = "force" ]; then
    echo "Fetching Blockchain data..." >&2
    mkdir -p $LMDB && cd $LMDB || errorExit 4 "Cannot create $LMDB dir!"
     rm -f data.mdb.zsync
     wget "$ZSYNC_URL" && zsync data.mdb.zsync
     if ! [ -f data.mdb ]; then
        errorExit 4 "Cannot fetch Blockchain data!"
     fi
     localsum=$(sha256sum data.mdb | cut -d ' ' -f 1)
     remotesum=$(wget -O- $ZSYNC_DATA_SHA)
     if [ "$localsum" != "$remotesum" ]; then
        errorExit 4 "Blockchain data corrupted!"
     fi
     echo "Blockchain data downloaded!" >&2
  else
    echo "Blockchain data already exists. Skipping fetching." >&2
  fi
}

runDaemon(){
    if [ -t 0 ] ; then
        prepareLmdb
        echo "Starting lethean daemon..." >&2
        letheand "$@"
    else
        errorExit 3 "You must allocate TTY to run letheand! Use -t option"
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
    lethean-wallet-cli --mnemonic-language English --generate-new-wallet "$CONF/$WALLETFILE" --daemon-host $DAEMON_HOST \
       --restore-height 254293 --password "$WALLETPASS" --log-file /dev/stdout --log-level 4 --command exit \
         || { errorExit 2 "Cannot create Wallet file! "; }
    WALLET=$(cat "$CONF/${WALLETFILE}.address.txt")
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
    cd /opt/lthn/var
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
    if [ -z "$DAEMON_HOST" ]; then
        runDaemon
    fi
    if [ -f "$CONF/$WALLETFILE" ]; then
      rm -f lethean-wallet-vpn-rpc*.login
      lethean-wallet-vpn-rpc --vpn-rpc-bind-port 14660 --wallet-file "$CONF/$WALLETFILE" --daemon-host $DAEMON_HOST --rpc-login 'dispatcher:SecretPass' --password "$WALLETPASS" --log-file /var/log/wallet.log &
      sleep 4
    else
      echo "Wallet file $CONF/$WALLETFILE is not inside container." >&2
    fi
    unset HTTP_PROXY
    unset http_proxy    
    shift
    while ! curl http://localhost:14660 >/dev/null 2>/dev/null; do
        echo "Waiting for walet rpc server."
        sleep 5
    done
    echo "Starting dispatcher" >&2
    exec lthnvpnd --syslog "$@"
    ;;

zsync-make)
    if [ -d "$LMDB" ]; then
        cd $LMDB
        zsyncmake -v -b 262144 -f data.mdb -u "$ZSYNC_DATA_URL" data.mdb
        sha256sum data.mdb | cut -d ' ' -f 1 >data.mdb.sha256
    else
        errorExit 2 "LMDB database does not exist!"
    fi
    ;;

sync-bc)
    shift
    prepareLmdb force
    ;;

letheand)
    shift
    runDaemon "$@"
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
    echo "Bad command. Use one of:"
    echo "run [args] to run dispatcher"
    echo "list [args] to list available services"
    echo "connect uri [args] to run client"
    echo "letheand [args] to run letheand"
    echo "easy-deploy [args] to easy deploy node"
    echo "upload-sdp [args] to upload SDP"
    echo "sync-bc to fast sync blockhain data from server."
    echo "sh to go into shell" 
    exit 2
    ;;
esac
